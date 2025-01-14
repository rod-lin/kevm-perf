"""
module <id>-SYNTAX

syntax SORT1
syntax SORT2
...

syntax SORT1 ::= <cons/op>(SORT2, SORT2, SORT1, ...) [function]

...

endmodule

module <id>

configuration <k> $PGM:K </k>

rule <term> => <term>
  requires <conditions>

...

endmodule
"""

import os
import argparse

from io import TextIOBase

from rec.spec import RECSpec
from rec.ast import RECTerm, RECVariable
from rec.parser import RECSpecParser


class RECToKTranspiler:
    def encode_ident(self, ident):
        return ident.replace("'", "_prime_").replace("\"", "_second_")

    def wrap_sort_name(self, sort, is_result):
        return "REC" + self.encode_ident(sort).replace("_", "") + ("Result" if is_result else "")

    def wrap_function_name(self, name):
        return "rec" + self.encode_ident(name).replace("_", "")

    def wrap_variable_name(self, name):
        return "REC_V_" + self.encode_ident(name)

    def write_signature(self, out, signature, is_cons, is_function=False):
        if is_cons:
            if self.heating:
                # if this is a constructor
                # we need to emit two syntax rules
                # one for result and one for non-result
                nonresult_args = ", ".join([ self.wrap_sort_name(sort, False) for sort in signature.input_sorts ])
                result_args = ", ".join([ self.wrap_sort_name(sort, True) for sort in signature.input_sorts ])
                out.write(f"syntax {self.wrap_sort_name(signature.output_sort, False)} ::= {self.wrap_function_name(signature.name)}({nonresult_args})")
                if len(nonresult_args):
                    out.write(" [seqstrict]\n")
                else:
                    out.write("\n")
                out.write(f"syntax {self.wrap_sort_name(signature.output_sort, True)} ::= {self.wrap_function_name(signature.name)}({result_args})\n")
            else:
                args = ", ".join([ self.wrap_sort_name(sort, False) for sort in signature.input_sorts ])
                out.write(f"syntax {self.wrap_sort_name(signature.output_sort, False)} ::= {self.wrap_function_name(signature.name)}({args})\n")
        else:
            args = ", ".join([ self.wrap_sort_name(sort, False) for sort in signature.input_sorts ])
            out.write(f"syntax {self.wrap_sort_name(signature.output_sort, False)} ::= {self.wrap_function_name(signature.name)}({args})")
            if is_function:
                out.write(" [function]\n")
            elif len(args):
                out.write(" [seqstrict]\n")
            else:
                out.write("\n")

    def write_term(self, out, term):
        if isinstance(term, RECTerm):
            out.write(f"{self.wrap_function_name(term.signature.name)}(")
            for i, arg in enumerate(term.arguments):
                if i != 0: out.write(", ")
                self.write_term(out, arg)
            out.write(")")
        elif isinstance(term, RECVariable):
            if self.heating:
                out.write(f"{self.wrap_variable_name(term.symbol)}:{self.wrap_sort_name(term.sort, True)}")
            else:
                out.write(f"{self.wrap_variable_name(term.symbol)}:{self.wrap_sort_name(term.sort, False)}")
        else:
            raise Exception(f"cannot transpile {term}")

    def write_condition(self, out, condition):
        assert condition.predicate in [ "eq", "neq" ]
        self.write_term(out, condition.left)
        if condition.predicate == "eq":
            out.write(" ==K ")
        elif condition.predicate == "neq":
            out.write(" =/=K ")
        self.write_term(out, condition.right)

    def write_rule(self, out, rule):
        out.write("rule ")
        self.write_term(out, rule.left)
        out.write(" => ")
        self.write_term(out, rule.right)
        out.write("\n")

        if len(rule.conditions):
            for i, condition in enumerate(rule.conditions):
                if i == 0:
                    out.write("  requires ")
                else:
                    out.write("   andBool ")
                self.write_condition(out, condition)
                out.write("\n")

    def find_functions_in_conditions(self, spec):
        functions = set()

        for rule in spec.rules:
            for cond in rule.conditions:
                functions = functions.union(cond.get_ops())

        # do this iteratively until no function symbols are added
        while True:
            updated = False
            for rule in spec.rules:
                # all ops that a function depends on
                # should be marked as functions
                if rule.left.signature.name in functions:
                    new_functions = rule.right.get_ops()
                    if len(new_functions.difference(functions)) != 0:
                        updated = True
                        functions = functions.union(new_functions)
            if not updated:
                break

        # remove all constructors
        return functions.difference(spec.env.cons_map.keys())

    def transpile(self, out: TextIOBase, spec: RECSpec):
        functions = self.find_functions_in_conditions(spec)

        # define syntax module
        out.write(f"module {spec.name.upper()}-SYNTAX\n\n")

        if self.heating:
            # use heating cooling rules
            for sort in spec.env.sorts:
                out.write(f"syntax {self.wrap_sort_name(sort, True)}\n")
            out.write(f"\n")

            for sort in spec.env.sorts:
                out.write(f"syntax {self.wrap_sort_name(sort, False)} ::= {self.wrap_sort_name(sort, True)}\n")
            out.write(f"\n")

            for sort in spec.env.sorts:
                out.write(f"syntax KResult ::= {self.wrap_sort_name(sort, True)}\n")

            out.write(f"syntax KItem ::= then(KItem, KItem) [seqstrict]\n")

            for cons_name in spec.env.cons_map:
                signature = spec.env.cons_map[cons_name]
                self.write_signature(out, signature, True)

            for op_name in spec.env.opns_map:
                signature = spec.env.opns_map[op_name]
                self.write_signature(out, signature, False, op_name in functions)
        else:
            # use function rules
            for sort in spec.env.sorts:
                out.write(f"syntax {self.wrap_sort_name(sort, False)}\n")

            out.write(f"\n")

            out.write(f"syntax KItem ::= then(KItem, KItem)\n")
            
            for cons_name in spec.env.cons_map:
                signature = spec.env.cons_map[cons_name]
                self.write_signature(out, signature, True)

            for op_name in spec.env.opns_map:
                signature = spec.env.opns_map[op_name]
                self.write_signature(out, signature, False, True)


        out.write(f"\nendmodule\n\n")

        # define main module
        out.write(f"module {spec.name.upper()}\n")

        out.write(f"imports K-EQUAL\n")
        out.write(f"imports {spec.name.upper()}-SYNTAX\n\n")

        for rule in spec.rules:
            self.write_rule(out, rule)

        # write terms to evaluate in a EvalList

        if self.inline_eval:
            out.write("\n")
            out.write("configuration <k>\n")
            for i, term in enumerate(spec.evals):
                if i < len(spec.evals) - 1:
                    out.write("  then(")
                else:
                    out.write("       ")

                self.write_term(out, term)
        
                if i < len(spec.evals) - 1:
                    out.write(",\n")
                else:
                    out.write("\n")

            out.write("  " + ")" * (len(spec.evals) - 1) + "\n")
            out.write("</k>\n")
        else:
            out.write("\n")
            for term in spec.evals:
                out.write("// eval: ")
                self.write_term(out, term)
                out.write("\n")

        out.write(f"\nendmodule\n")

    # if inline_eval, put all the terms to eval
    # in the module definition
    def __init__(self, inline_eval=False, heating=False):
        self.inline_eval = inline_eval
        self.heating = heating


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="a .rec file or a directory containing .rec files")
    parser.add_argument("-o", dest="output", help="directory to put the output k modules")
    parser.add_argument("--inline-eval", action="store_const", const=True, default=False, help="inline eval section in the k modules generated")
    parser.add_argument("--heating", action="store_const", const=True, default=False, help="use heating/cooling rules instead of using all function constructs")
    parser.add_argument("-I", dest="include_path", action="append", default=[], help="add an include path to the REC loader")
    args = parser.parse_args()

    if os.path.isfile(args.input):
        rec_files = [ args.input ]
    elif os.path.isdir(args.input):
        rec_files = []

        for file_name in os.listdir(args.input):
            if file_name.endswith(".rec"):
                complete_path = os.path.join(args.input, file_name)
                rec_files.append(complete_path)
    else:
        raise Exception(f"no such file or directory {args.input}")

    if not os.path.exists(args.output):
        os.mkdir(args.output)

    assert os.path.isdir(args.output)

    parser = RECSpecParser(include_path=args.include_path)
    transpiler = RECToKTranspiler(inline_eval=args.inline_eval, heating=args.heating)

    for rec_file in rec_files:
        print(f"converting {rec_file}")

        spec = parser.load(rec_file)
        output_file = os.path.join(args.output, spec.name.lower() + ".k")

        with open(output_file, "w") as f:
            transpiler.transpile(f, spec)


if __name__ == "__main__":
    main()
