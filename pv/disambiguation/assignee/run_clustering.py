import os
import pickle

import numpy as np
import wandb
from absl import app
from absl import flags
from absl import logging
from grinch.agglom import Agglom
from grinch.model import LinearAndRuleModel

from pv.disambiguation.assignee.load_name_mentions import Loader
from pv.disambiguation.assignee.model import AssigneeModel
import configparser

logging.set_verbosity(logging.INFO)


def batched_canopy_process(datasets, model, encoding_model):
    logging.info('running on batch of %s with %s points', len(datasets), sum([len(x[1]) for x in datasets]))
    all_pids = []
    all_lbls = []
    all_records = []
    all_canopies = []
    for dataset_name, dataset in datasets:
        pids, lbls, records = dataset[0], dataset[1], dataset[2]
        all_canopies.extend([dataset_name for _ in range(len(pids))])
        all_pids.extend(pids)
        all_lbls.extend(lbls)
        all_records.extend(records)
    return run_on_batch(all_pids, all_lbls, all_records, all_canopies, model, encoding_model)


def run_on_batch(all_pids, all_lbls, all_records, all_canopies, model, encoding_model, canopy2predictions):
    features = encoding_model.encode(all_records)
    grinch = Agglom(model, features, num_points=len(all_pids), min_allowable_sim=0)
    grinch.build_dendrogram_hac()
    fc = grinch.flat_clustering(model.aux['threshold'])
    # import pdb
    # pdb.set_trace()
    for i in range(len(all_pids)):
        if all_canopies[i] not in canopy2predictions:
            canopy2predictions[all_canopies[i]] = [[], []]
        canopy2predictions[all_canopies[i]][0].append(all_pids[i])
        canopy2predictions[all_canopies[i]][1].append('%s-%s' % (all_canopies[i], fc[i]))
    return canopy2predictions


def needs_predicting(canopy_list, results, loader):
    return [c for c in canopy_list if c not in results]


def batcher(canopy_list, loader, min_batch_size=800):
    all_pids = []
    all_lbls = []
    all_records = []
    all_canopies = []
    for c in canopy_list:
        if len(all_pids) > min_batch_size:
            yield all_pids, all_lbls, all_records, all_canopies
            all_pids = []
            all_lbls = []
            all_records = []
            all_canopies = []
        records = loader.load(c)
        pids = [x.uuid for x in records]
        lbls = -1 * np.ones(len(records))
        all_canopies.extend([c for _ in range(len(pids))])
        all_pids.extend(pids)
        all_lbls.extend(lbls)
        all_records.extend(records)
    if len(all_pids) > 0:
        yield all_pids, all_lbls, all_records, all_canopies


def run_batch(config, canopy_list, outdir, loader, job_name='disambig'):
    logging.info('need to run on %s canopies = %s ...', len(canopy_list), str(canopy_list[:5]))

    os.makedirs(outdir, exist_ok=True)
    results = dict()
    outfile = os.path.join(outdir, job_name) + '.pkl'
    num_mentions_processed = 0
    if os.path.exists(outfile):
        with open(outfile, 'rb') as fin:
            results = pickle.load(fin)

    to_run_on = needs_predicting(canopy_list, results, None)
    logging.info('had results for %s, running on %s', len(canopy_list) - len(to_run_on), len(to_run_on))

    if len(to_run_on) == 0:
        logging.info('already had all canopies completed! wrapping up here...')

    encoding_model = AssigneeModel.from_config(config)
    weight_model = LinearAndRuleModel.from_encoding_model(encoding_model)
    weight_model.aux['threshold'] = 1 / (1 + config['assignee']['sim_threshold'])

    if to_run_on:
        for idx, (all_pids, all_lbls, all_records, all_canopies) in enumerate(
          batcher(to_run_on, loader, int(config['assignee']['min_batch_size']))):
            logging.info('[%s] run_batch %s - %s - processed %s mentions', job_name, idx, len(canopy_list),
                         num_mentions_processed)
            run_on_batch(all_pids, all_lbls, all_records, all_canopies, weight_model, encoding_model, results)
            # if idx % 10 == 0:
            #     wandb.log({'computed': idx + int(config['assignee']['chunk_id']) * int(config['assignee']['chunk_size']), 'num_mentions': num_mentions_processed})
            #     logging.info('[%s] caching results for job', job_name)
            #     with open(outfile, 'wb') as fin:
            #         pickle.dump(results, fin)

    with open(outfile, 'wb') as fin:
        pickle.dump(results, fin)


def handle_singletons(canopy2predictions, singleton_canopies, loader):
    for s in singleton_canopies:
        ments = loader.load(s)
        assert len(ments) == 1
        canopy2predictions[s] = [[ments[0].uuid], [ments[0].uuid]]
    return canopy2predictions


def run_singletons(canopy_list, outdir, loader, job_name='disambig'):
    logging.info('need to run on %s canopies = %s ...', len(canopy_list), str(canopy_list[:5]))

    os.makedirs(outdir, exist_ok=True)
    results = dict()
    outfile = os.path.join(outdir, job_name) + '.pkl'
    num_mentions_processed = 0
    if os.path.exists(outfile):
        with open(outfile, 'rb') as fin:
            results = pickle.load(fin)

    to_run_on = needs_predicting(canopy_list, results, loader)
    logging.info('had results for %s, running on %s', len(canopy_list) - len(to_run_on), len(to_run_on))

    if len(to_run_on) == 0:
        logging.info('already had all canopies completed! wrapping up here...')

    if to_run_on:
        handle_singletons(results, to_run_on, loader)

    with open(outfile, 'wb') as fin:
        pickle.dump(results, fin)


def main(argv):
    logging.info('Running clustering - %s ', str(argv))

    config = configparser.ConfigParser()
    config.read(['config/database_config.ini', 'config/assignee/run_clustering.ini'])

    # wandb.init(project="%s-%s" % (config['assignee']['exp_name'], config['assignee']['dataset_name']))
    # wandb.config.update(config)

    loader = Loader.from_config(config)
    all_canopies = set(loader.assignee_canopies.keys())
    all_canopies = set([x for x in all_canopies if loader.num_records(x) < int(config['assignee']['max_canopy_size'])])
    singletons = set([x for x in all_canopies if loader.num_records(x) == 1])
    all_canopies_sorted = sorted(list(all_canopies.difference(singletons)), key=lambda x: (loader.num_records(x), x),
                                 reverse=True)
    logging.info('Number of canopies %s ', len(all_canopies_sorted))
    logging.info('Number of singletons %s ', len(singletons))
    logging.info('Largest canopies - ')
    for c in all_canopies_sorted[:10]:
        logging.info('%s - %s records', c, loader.num_records(c))
    outdir = os.path.join(config['assignee']['outprefix'], 'assignee', config['assignee']['run_id'])
    num_chunks = int(len(all_canopies_sorted) / int(config['assignee']['chunk_size']))
    logging.info('%s num_chunks', num_chunks)
    logging.info('%s chunk_size', int(config['assignee']['chunk_size']))
    logging.info('%s chunk_id', int(config['assignee']['chunk_id']))
    chunks = [[] for _ in range(num_chunks)]
    for idx, c in enumerate(all_canopies_sorted):
        chunks[idx % num_chunks].append(c)

    if int(config['assignee']['chunk_id']) == 0:
        logging.info('Running singletons!!')
        run_singletons(list(singletons), outdir, job_name='job-singletons', loader=loader)

    run_batch(config, chunks[int(config['assignee']['chunk_id'])], outdir, loader, job_name='job-%s' % int(config['assignee']['chunk_id']))


if __name__ == "__main__":
    app.run(main)
