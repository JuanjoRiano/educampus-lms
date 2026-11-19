"""Compute AST-based cyclomatic complexity using documented decision rules."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'educampus'/'service.py'


def complexity(func: ast.FunctionDef):
    branches=[]
    for node in ast.walk(func):
        if isinstance(node,ast.If): branches.append(('if',node.lineno,1))
        elif isinstance(node,(ast.For,ast.AsyncFor,ast.While)): branches.append(('loop',node.lineno,1))
        elif isinstance(node,ast.ExceptHandler): branches.append(('except',node.lineno,1))
        elif isinstance(node,ast.IfExp): branches.append(('conditional expression',node.lineno,1))
        elif isinstance(node,ast.BoolOp): branches.append(('short-circuit boolean',node.lineno,len(node.values)-1))
        elif isinstance(node,(ast.ListComp,ast.SetComp,ast.DictComp,ast.GeneratorExp)):
            branches.append(('comprehension loop',node.lineno,len(node.generators)))
            branches.extend(('comprehension guard',node.lineno,len(g.ifs)) for g in node.generators if g.ifs)
    return {'function':func.name,'predicate_count':sum(x[2] for x in branches),'vG':1+sum(x[2] for x in branches),'decisions':[{'type':kind,'line':line,'increment':count} for kind,line,count in branches]}


def main():
    tree=ast.parse(TARGET.read_text(encoding='utf-8'))
    names={'_academic_rules'}
    output=[complexity(node) for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
    for cls in tree.body:
        if isinstance(cls,ast.ClassDef) and cls.name in {'EnrollmentService','SQLiteEnrollmentRepository'}:
            output.extend(complexity(node) | {'function':cls.name+'.'+node.name} for node in cls.body if isinstance(node,ast.FunctionDef) and node.name in {'execute','confirm'})
    dst=ROOT.parent/'calidad'/'complejidad_mccabe.json'
    dst.write_text(json.dumps({'method':'Python AST: each if/loop/except/conditional expression, short-circuit operand and comprehension increments P; v(G)=P+1','functions':output},ensure_ascii=False,indent=2))
    print(json.dumps(output,indent=2))

if __name__=='__main__':main()
