from scipy.optimize import linprog
import argparse
import csv
import numpy as np

class Producer:
    def __init__(self, name, input_table, output_commodity, max_output):
        self.name = name
        self.input_table = input_table
        self.output_commodity = output_commodity
        self.max_output = max_output

class App:
    def __init__(self, prod_table_f, supply_table_f, demand_table_f, priorities_table_f, time_period):
        self.production_table = {}
        self.commodity_names = set()
        self.producers = {}
        self.materials_table = {}
        self.producable_commodities = set()
        self.priorities_table = {}
        self.prod_table_f = prod_table_f
        self.supply_table_f = supply_table_f
        self.demand_table_f = demand_table_f
        self.priorities_table_f = priorities_table_f
        self.plan = []
        self.time_period = time_period

    def run(self):
        self.read_tables()

        self.run_balancing()
        self.print_results()

    def read_tables(self):
        self.read_production_table()

        self.initialize_blank_supply_table()
        self.initialize_blank_demand_table()
        self.initialize_blank_materials_table()

        self.read_supply_table()
        self.read_demand_table()
        self.read_priorities_table()

    def initialize_blank_production_table(self):
        for producer_name in self.producers:
            self.production_table[producer_name] = 0.0

    def initialize_blank_supply_table(self):
        self.supply_table = {commodity: 0.0 for commodity in self.commodity_names}

    def initialize_blank_demand_table(self):
        self.demand_table = {commodity: 0.0 for commodity in self.commodity_names}

    def initialize_blank_materials_table(self):
        self.materials_table = {commodity: 0.0 for commodity in self.commodity_names}

    def read_production_table(self):
        reader = csv.reader(self.prod_table_f)
        reader.__next__()

        for row in reader:
            assert len(row) == 5
            row = [s.strip() for s in row]
            (producer_name, output_commodity, input_commodity, input_amount, max_output) = row
            self.commodity_names.add(output_commodity)
            self.commodity_names.add(input_commodity)
            self.producable_commodities.add(output_commodity)
            try:
                input_amount = float(input_amount)
                max_output = float(max_output)
                assert input_amount > -1e-5
                max_output = 4294967296 if max_output < 0 else max_output

            except ValueError:
                assert False
            except:
                assert False
            if self.producers.get(producer_name, None) is None:
                self.producers[producer_name] = Producer(producer_name, {input_commodity: input_amount}, output_commodity, max_output)
            else:
                producer = self.producers[producer_name]
                assert input_commodity not in producer.input_table
                assert output_commodity == producer.output_commodity
                assert abs(max_output - producer.max_output) < 1e-5
                producer.input_table[input_commodity] = input_amount
    
    def read_supply_table(self):
        reader = csv.reader(self.supply_table_f)
        reader.__next__()
        for row in reader:
            assert len(row) == 3
            row = [s.strip() for s in row]
            (commodity, amount, is_inflow) = row
            if commodity in self.commodity_names:
                try:
                    amount = float(amount) * self.time_period if is_inflow == "1" else float(amount)
                    assert amount > 0
                except ValueError:
                    assert False
                except:
                    assert False

                self.supply_table[commodity] += amount

    def read_demand_table(self):
        reader = csv.reader(self.demand_table_f)
        reader.__next__()
        for row in reader:
            assert len(row) == 3
            row = [s.strip() for s in row]
            (commodity, amount, is_outflow) = row
            if commodity in self.commodity_names:
                try:
                    amount = float(amount) * self.time_period if is_outflow == "1" else float(amount)
                    assert amount > 0
                except ValueError:
                    assert False
                except:
                    assert False

                self.demand_table[commodity] += amount

    def read_priorities_table(self):
        reader = csv.reader(self.priorities_table_f)
        reader.__next__()

        for row in reader:
            assert len(row) == 2
            (commodity, importance) = row
            assert commodity in self.commodity_names
            assert self.priorities_table.get(commodity, None) is None
            try:
                self.priorities_table[commodity] = float(importance)
            except ValueError:
                assert False
            except:
                assert False
            
        for commodity in self.commodity_names:
            if self.priorities_table.get(commodity, None) is None:
                self.priorities_table[commodity] = 0.0

    def set_initial_materials_table(self):
        for commodity in self.commodity_names:
            self.materials_table[commodity] += self.supply_table[commodity]
            self.materials_table[commodity] -= self.demand_table[commodity]

    def producable_commodities(self):
        return [commodity for commodity in self.commodity_names if commodity in self.producable_commodities]

    def in_demand_commodities(self):
        return [commodity for commodity in self.commodity_names if self.materials_table[commodity] < 0]

    def production_cost(self, amount, producer):
        return {c: self.producers[producer.name].input_table.get(c, 0) * amount for c in self.commodity_names}

    def max_production_amount(self, producer: Producer):
        #Must be in demand
        commodity = producer.output_commodity
        demand = min(-self.materials_table[commodity], producer.max_output - self.production_table[producer.name])
        if demand < 1e-5:
            return (0.0, 0.0)
        else:
            cost = self.production_cost(demand, producer)
            min_ratio = 1.0
            for c in self.commodity_names:
                if cost[c] > 0.0:
                    ratio = self.materials_table[c] / cost[c]
                    min_ratio = min(ratio, min_ratio)
            return (demand * min_ratio, min_ratio)

    def produce(self, amount, producer):
        assert amount > 0
        commodity = producer.output_commodity
        cost = self.production_cost(amount, producer)
        self.materials_table = {c: self.materials_table[c] - cost[c] for c in self.commodity_names}
        self.materials_table[commodity] += amount
        self.production_table[producer.name] += amount

    def run_linprog(self):
        l_commodity_names = sorted(list(set(self.commodity_names)))
        n_commodities = len(l_commodity_names)
        commodity_numbers = {l_commodity_names[i]: i for i in range(n_commodities)}
        producer_names = sorted(list(self.producers))
        n_producers = len(producer_names)

        bounds = [(0, self.producers[producer_name].max_output) for producer_name in producer_names] 
        production_input_coefficients = np.zeros((n_producers, n_commodities))
        production_output_coefficients = np.zeros((n_producers, n_commodities))

        c = np.zeros((n_producers,))
        for i in range(n_producers):
            producer = self.producers[producer_names[i]]
            output_commodity = producer.output_commodity
            c[i] += self.priorities_table[output_commodity]
            for (commodity_name, amount) in producer.input_table.items():
                c[i] -= self.priorities_table[commodity_name] * amount
        c = -c

        supply = np.zeros((n_commodities,))
        demand = np.zeros((n_commodities,))

        for commodity_name in l_commodity_names:
            supply[commodity_numbers[commodity_name]] = self.supply_table[commodity_name]
            demand[commodity_numbers[commodity_name]] = self.demand_table[commodity_name]

        for (i, producer_name) in enumerate(producer_names):
            producer = self.producers[producer_name]
            j = commodity_numbers[producer.output_commodity]
            production_output_coefficients[i, j] = 1
            for (input_commodity_name, input_commodity_amount) in producer.input_table.items():
                production_input_coefficients[i, commodity_numbers[input_commodity_name]] = input_commodity_amount

        equations_ub_A = np.zeros((n_commodities, n_producers))
        equations_ub_b = np.zeros((n_commodities,))

        for j in range(n_commodities):
            prod = 0
            cons = 0
            for i in range(n_producers):
                equations_ub_A[j, i] = production_output_coefficients[i, j] - production_input_coefficients[i, j]
            equations_ub_b[j] = supply[j] - demand[j]

        equations_ub_A = -equations_ub_A

        self.lp_res = linprog(c, A_ub=equations_ub_A, b_ub=equations_ub_b, bounds=bounds)

    def run_balancing(self):
        self.plan.clear()
        self.set_initial_materials_table()
        self.initialize_blank_production_table()

        self.run_linprog()
        l_commodity_names = sorted(list(set(self.commodity_names)))
        n_commodities = len(l_commodity_names)
        commodity_numbers = {l_commodity_names[i]: i for i in range(n_commodities)}
        producer_names = sorted(list(self.producers))

        if self.lp_res.status == 0:
            for (i, amount) in enumerate(self.lp_res.x):
                producer = self.producers[producer_names[i]]
                if amount > 0:
                    self.plan.append((producer.name, amount, producer.output_commodity, self.production_cost(amount, producer)))
                    self.produce(amount, producer)        

    def is_balanced(self):
        return all(self.materials_table[c] >= 0.0 for c in self.materials_table)

    def unbalanced_commodities(self):
        return [c for c in self.materials_table if self.materials_table[c] < 0.0]

    def balanced_commodities(self):
        return [c for c in self.materials_table if self.materials_table[c] >= 0.0]

    def print_results(self):
        print("Output:")
        print()
        print("Result: {}".format(self.lp_res.fun))
        print("Output Vector: {}".format(self.lp_res.x))
        print("Message: {}".format(self.lp_res.message))

        if self.lp_res.status == 0:
            print()
            print("Production Plan")
            for action in self.plan:
                (producer_name, amount, commodity, cost_dict) = action
                costs = sorted([(c, amount) for (c, amount) in cost_dict.items() if amount > 0.0], key=lambda x: x[0])
                print("    Produce {:.3f} units of {} at {} using".format(amount, commodity, producer_name))
                for (c, amount) in costs:
                    print("        {:.3f} units of {}".format(amount, c))

        print()
        if self.lp_res.status == 0:
            print("Plan is feasible")
            print()
            print("Commodities")
            for c in sorted(self.balanced_commodities()):
                print("    {}: {:.4f} surplus - {:.4f} demanded".format(c, self.materials_table[c], self.demand_table[c]))
        else:
            print("Plan is infeasible")

        if self.lp_res.status == 0:
            print()
            print("Final State")
            for c in sorted(self.commodity_names):
                print("    {}: {:.4f} -> {:.4f}".format(c, self.supply_table[c], self.materials_table[c] + self.demand_table[c]))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('production_file', type=open, nargs=1)
    parser.add_argument('inputs_file', type=open, nargs=1)
    parser.add_argument('outputs_file', type=open, nargs=1)
    parser.add_argument('commodity_importance_file', type=open, nargs=1)
    parser.add_argument('time_peroid', type=float, nargs=1, default=0)

    #commodities.csv inputs.csv outputs.csv
    #inputs.csv
    #outputs.csv

    args = parser.parse_args()

    app = App(args.production_file[0], args.inputs_file[0], 
              args.outputs_file[0], args.commodity_importance_file[0], args.time_peroid[0])
    app.run()