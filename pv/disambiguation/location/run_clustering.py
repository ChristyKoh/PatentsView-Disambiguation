import collections
import os
import pickle

import numpy as np
import wandb
from absl import app
from absl import flags
from absl import logging
from grinch.model import LinearAndRuleModel

from pv.disambiguation.location.load import Loader
from pv.disambiguation.location.model import LocationAgglom, LocationModelWithApps

FLAGS = flags.FLAGS

flags.DEFINE_string('inventor_location_name_mentions', 'data/location/inventor_location.mentions.pkl', '')
flags.DEFINE_string('assignee_location_name_mentions', 'data/location/assignee_location.mentions.pkl', '')

flags.DEFINE_string('outprefix', 'exp_out', 'data path')
flags.DEFINE_string('run_id', 'run_1', 'data path')

flags.DEFINE_string('dataset_name', 'patentsview', '')
flags.DEFINE_string('exp_name', 'disambiguation-location', '')

flags.DEFINE_string('base_id_file', '', '')

flags.DEFINE_integer('chunk_size', 10000, '')
flags.DEFINE_integer('chunk_id', 1000, '')
flags.DEFINE_integer('min_batch_size', 1, '')

flags.DEFINE_integer('max_canopy_size', 900, '')

logging.set_verbosity(logging.INFO)


def run_on_batch(all_pids, all_lbls, all_records, all_canopies, model, encoding_model, canopy2predictions):
    features = encoding_model.encode(all_records)
    grinch = LocationAgglom(model, features, num_points=len(all_pids))
    grinch.build_dendrogram_hac()
    fc = grinch.flat_clustering(model.aux['threshold'])
    canopy2cluster2mentions = dict()
    for i in range(len(all_pids)):
        if all_canopies[i] not in canopy2cluster2mentions:
            canopy2cluster2mentions[all_canopies[i]] = collections.defaultdict(list)
        canopy2cluster2mentions[all_canopies[i]]['%s-%s' % (all_canopies[i], fc[i])].append(all_records[i])
    for canopy, cluster2mentions in canopy2cluster2mentions.items():
        if canopy not in canopy2predictions:
            canopy2predictions[canopy] = [[], []]
        for c, ments in cluster2mentions.items():
            eid = entity_id(ments)
            for m in ments:
                for mid in m.mention_ids:
                    canopy2predictions[canopy][0].append(mid)
                    canopy2predictions[canopy][1].append(eid)
    return canopy2predictions


def needs_predicting(canopy_list, results, loader):
    return [c for c in canopy_list if c not in results]


def batcher(canopy_list, loader, min_batch_size=1):
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


def run_batch(canopy_list, outdir, job_name='disambig'):
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

    encoding_model = LocationModelWithApps.from_flags(FLAGS)
    weight_model = LinearAndRuleModel.from_encoding_model(encoding_model)
    weight_model.aux['threshold'] = 0.1
    loader = Loader.from_flags(FLAGS)

    if to_run_on:
        for idx, (all_pids, all_lbls, all_records, all_canopies) in enumerate(
          batcher(to_run_on, loader, FLAGS.min_batch_size)):
            logging.info('[%s] run_batch %s - %s - processed %s mentions', job_name, idx, len(canopy_list),
                         num_mentions_processed)
            run_on_batch(all_pids, all_lbls, all_records, all_canopies, weight_model, encoding_model, results)
            if idx % 10000 == 0:
                wandb.log({'computed': idx + FLAGS.chunk_id * FLAGS.chunk_size, 'num_mentions': num_mentions_processed})
                logging.info('[%s] caching results for job', job_name)
                with open(outfile, 'wb') as fin:
                    pickle.dump(results, fin)

    with open(outfile, 'wb') as fin:
        pickle.dump(results, fin)


def entity_id(cluster_of_records):
    from collections import defaultdict
    counts = defaultdict(int)
    in_db = set()
    for r in cluster_of_records:
        r_str = '%s|%s|%s' % (r._canonical_city, r._canonical_state, r._canonical_country)
        if r._in_database == 1:
            in_db.add(r_str)
        counts[r_str] += 1
    if in_db:
        return max(in_db, key=lambda x: counts[x])
    else:
        return max(counts, key=lambda x: counts[x])


def handle_singletons(canopy2predictions, singleton_canopies, loader):
    for s in singleton_canopies:
        ments = loader.name_mentions[s]
        assert len(ments) == 1
        canopy2predictions[s] = [[], []]
        eid = entity_id(ments)
        for m in ments[0].mention_ids:
            canopy2predictions[s][0].append(m)
            canopy2predictions[s][1].append(eid)
    return canopy2predictions


def run_singletons(canopy_list, outdir, job_name='disambig'):
    logging.info('need to run on %s canopies = %s ...', len(canopy_list), str(canopy_list[:5]))

    os.makedirs(outdir, exist_ok=True)
    results = dict()
    outfile = os.path.join(outdir, job_name) + '.pkl'
    if os.path.exists(outfile):
        with open(outfile, 'rb') as fin:
            results = pickle.load(fin)

    loader = Loader.from_flags(FLAGS)

    to_run_on = needs_predicting(canopy_list, results, loader)
    logging.info('had results for %s, running on %s', len(canopy_list) - len(to_run_on), len(to_run_on))

    if len(to_run_on) == 0:
        logging.info('already had all canopies completed! wrapping up here...')

    if to_run_on:
        handle_singletons(results, to_run_on, loader)

    with open(outfile, 'wb') as fin:
        pickle.dump(results, fin)


def main(argv):
    logging.info('Running location clustering - %s ', str(argv))
    wandb.init(project="%s-%s" % (FLAGS.exp_name, FLAGS.dataset_name))
    wandb.config.update(flags.FLAGS)

    loader = Loader.from_flags(FLAGS)
    all_canopies = set(loader.name_mentions.keys())
    singletons = set([x for x in all_canopies if loader.num_records(x) == 1])
    all_canopies_sorted = sorted(list(all_canopies.difference(singletons)), key=lambda x: (loader.num_records(x), x),
                                 reverse=True)
    logging.info('Number of canopies %s ', len(all_canopies_sorted))
    logging.info('Number of singletons %s ', len(singletons))
    logging.info('Largest canopies - ')
    for c in all_canopies_sorted[:10]:
        logging.info('%s - %s records', c, loader.num_records(c))
    outdir = os.path.join(FLAGS.outprefix, 'location', FLAGS.run_id)
    num_chunks = int(len(all_canopies_sorted) / FLAGS.chunk_size)
    logging.info('%s num_chunks', num_chunks)
    logging.info('%s chunk_size', FLAGS.chunk_size)
    logging.info('%s chunk_id', FLAGS.chunk_id)
    chunks = [[] for _ in range(num_chunks)]
    for idx, c in enumerate(all_canopies_sorted):
        chunks[idx % num_chunks].append(c)

    if FLAGS.chunk_id == 0:
        logging.info('Running singletons!!')
        run_singletons(list(singletons), outdir, job_name='job-singletons')

    run_batch(chunks[FLAGS.chunk_id], outdir, job_name='job-%s' % FLAGS.chunk_id)


if __name__ == "__main__":
    app.run(main)
