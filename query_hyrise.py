import argparse
import logging
import multiprocessing.dummy
import pprint
import time

import requests
import tableprint


def contains_table(data):
    return 'header' in data and 'rows' in data


def query_hyrise(host, port, query, print_result=True):
    try:
        url = "http://{host}:{port}/query".format(host=host, port=port)
        data = "query={data}".format(data=query)
        result = requests.post(url, data).json()
        if print_result and contains_table(result):
            tableprint.table(result['rows'], result['header'])
        else:
            logging.warning(pprint.pformat(result, indent=20, width=120, compact=True))
    except requests.RequestException as e:
        logging.error(e)


def benchmark(host, port, query_file, num_threads, num_queries):
    # TODO: Ignore errors in preparation phase and invalidate benchmark on error during actual run
    with open(query_file) as query_f:
        query = query_f.read()

    queries = [(host, port, query)] * num_queries

    # Because of reasons, the first query on each node is executed with lower throughput.
    # So for accurate measurements, we need the query to be executed on every node at lest once.
    # As we don't know anything about the cluster structure at this point,
    # this benchmark may return lower throughput if num_queries < number of cluster nodes.
    logging.info("Benchmark {0}:{1} preparation...".format(host, port, num_queries, num_threads))
    with multiprocessing.dummy.Pool(num_threads) as pool:
        pool.starmap(query_hyrise, queries)
    logging.info("Benchmark {0}:{1} with {2} queries in {3} threads...".format(host, port, num_queries, num_threads))
    start = time.time()
    with multiprocessing.dummy.Pool(num_threads) as pool:
        pool.starmap(query_hyrise, queries)
    queries_second = num_queries / (time.time() - start)
    logging.info("Benchmark finished with {throughput} queries/s".format(throughput=queries_second))
    return queries_second


def main():
    parser = argparse.ArgumentParser(description='Query Hyrise')
    parser.add_argument('query_file')
    parser.add_argument('--host', default='127.0.0.1', type=str, help='Hyrise IP address')
    parser.add_argument('--port', default=5000, type=int, help='Hyrise port')
    parser.add_argument('--threads', default=1, type=int, help='Threads')
    parser.add_argument('--queries', default=1, type=int, help='Queries')
    args = parser.parse_args()

    query_file = args.query_file
    host = args.host
    port = args.port
    threads = args.threads
    num_queries = args.queries

    benchmark(host, port, query_file, threads, num_queries)


if __name__ == '__main__':
    main()
