import logging
import time

from ortools.linear_solver import pywraplp


class Vertex:
    def __init__(self, name):
        self.name = name
        self.outbound = []
        self.inbound = []
        self.departure = None
        self.arrival = None

    def selected_outbound(self):
        for e in self.outbound:
            if e.selected:
                return e
        return None

    def __repr__(self):
        return '<Vertex {0}>'.format(self.name)


class Edge:
    def __init__(self, start, end, duration):
        self.start = start
        self.end = end
        self.duration = duration
        self.selected = None
        self.departure = None
        self.arrival = None

    def __repr__(self):
        return '<Edge {0} {1}>'.format(self.start, self.end)


class Route:
    def __init__(self, edges):
        self.edges = edges

    def __repr__(self):
        return '<Route {0}>'.format(self.edges)


class Model:
    def __init__(self):
        self.vertices = []
        self.depot = None
        self.edges = []

    def add_vertex(self, name):
        vertex = Vertex(name)
        self.vertices.append(vertex)
        return vertex

    def set_depot(self, vertex):
        self.depot = vertex

    def add_edge(self, start, end, duration):
        edge = Edge(start, end, duration)
        start.outbound.append(edge)
        end.inbound.append(edge)
        self.edges.append(edge)
        return edge

    def _init_variables(self, solver):
        inf = solver.infinity()

        for i, v in enumerate(self.vertices):
            v.departure = solver.NumVar(0., inf, 'VDEP {0:d} {1}'.format(i, v))
            v.arrival = solver.NumVar(0., inf, 'VARR {0:d} {1}'.format(i, v))

        for i, e in enumerate(self.edges):
            e.selected = solver.BoolVar('SELECTED {0:d} {1}'.format(i, e))
            e.departure = solver.NumVar(0., inf, 'EDEP {0:d} {1}'.format(i, e))
            e.arrival = solver.NumVar(0., inf, 'EARR {0:d} {1}'.format(i, e))

    def _cleanup_variables(self):
        for i, v in enumerate(self.vertices):
            v.departure = None
            v.arrival = None

        for i, e in enumerate(self.edges):
            e.selected = None
            e.departure = None
            e.arrival = None

    def _burn_variables(self):
        for v in self.vertices:
            v.departure = v.departure.solution_value()
            v.arrival = v.arrival.solution_value()

        for e in self.edges:
            e.selected = e.selected.solution_value() >= 0.5
            if e.selected:
                e.departure = e.departure.solution_value()
                e.arrival = e.arrival.solution_value()
            else:
                e.departure = None
                e.arrival = None

    def _setup(self, solver_name):
        solver = pywraplp.Solver.CreateSolver('SCIP')
        # solver.EnableOutput()

        self._init_variables(solver)

        max_time = sum([e.duration for e in self.edges])

        for v in self.vertices:
            solver.Add(sum([e.selected for e in v.outbound]) == 1)
            solver.Add(sum([e.selected for e in v.inbound]) == 1)
            if v != self.depot:
                solver.Add(v.departure == v.arrival)
            else:
                solver.Add(v.departure == 0)
                solver.Add(v.arrival >= v.departure)
            solver.Add(v.departure == sum([e.departure for e in v.outbound]))
            solver.Add(v.arrival == sum([e.arrival for e in v.inbound]))

        for e in self.edges:
            solver.Add(e.arrival - e.departure == e.duration * e.selected)
            solver.Add(e.arrival <= max_time * e.selected)

        solver.Minimize(sum([e.selected * e.duration for e in self.edges]))

        logging.debug('%d variables', solver.NumVariables())
        logging.debug('%d constraints', solver.NumConstraints())
        return solver

    def _solve(self, solver):
        logging.info('Solver started')
        start_at = time.time()
        status = solver.Solve()
        end_at = time.time()
        logging.info('Solver finished in %.2f seconds', end_at - start_at)

        if status != pywraplp.Solver.OPTIMAL:
            logging.info('Optimal solution not found')
            self._cleanup_variables()
            return None

        objective = solver.Objective().Value()
        logging.debug('Objective value %.2f', objective)

        self._burn_variables()

        return objective

    def _solution(self):
        edges = []
        at = self.depot
        while True:
            edge = at.selected_outbound()
            if edge is None:
                return None
            if edge in edges:
                return None
            edges.append(edge)
            at = edge.end
            if at == self.depot:
                break
        return Route(edges)

    def solve(self):
        solver = self._setup('SCIP')

        objective = self._solve(solver)
        if objective is None:
            return None

        return self._solution()
