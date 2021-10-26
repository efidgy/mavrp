import json
import sys
import logging

from .model import Model


def usage():
    print('''
mavrp-salesman INPUT [MAX_SIZE]

    INPUT    -- path to json input.
    MAX_SIZE -- max problem size.
''', file=sys.stderr)


def parse_args(argv):
    if len(argv) < 2:
        usage()
        sys.exit(1)
    filename = argv[1]
    max_size = int(argv[2]) if len(argv) > 2 else None
    return filename, max_size


def load_data(filename):
    with open(filename, 'r') as f:
        return json.load(f)


def build_model(data, max_size=None):
    matrix = data['matrix']
    size = min(max_size, len(matrix)) if max_size is not None else len(matrix)

    model = Model()

    vertices = {}
    for i in range(size):
        vertices[i] = model.add_vertex('{0:d}'.format(i))

    model.set_depot(vertices[data['depot']])

    for i in range(size):
        for j in range(size):
            if i == j:
                continue
            if matrix[i][j] == 0:
                continue
            model.add_edge(vertices[i], vertices[j], matrix[i][j])

    return model


def print_schedule(route):
    if not route.edges:
        return
    edge = route.edges[0]
    print('{0} {1:.2f}'.format(edge.start, edge.departure))
    for edge in route.edges:
        print('{0} {1:.2f}'.format(edge.end, edge.arrival))


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)-15s %(levelname)-8s %(message)s',
    )

    filename, max_size = parse_args(sys.argv)
    data = load_data(filename)
    model = build_model(data, max_size=max_size)

    print('{0:d} vertices'.format(len(model.vertices)))
    print('{0:d} edges'.format(len(model.edges)))
    route = model.solve()

    if route is None:
        print('Route not found')
    else:
        print_schedule(route)


if __name__ == '__main__':
    main()
