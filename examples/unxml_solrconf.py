#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" simplify solrconfig.xml dump as json """

import unxml

bool_name_to_val=dict(true=True,false=False)
solr_type_to_caster=dict(bool=lambda v: bool_name_to_val[v],
                         float=float,
                         int=int,
                         str=unicode)

def nt_solr_untype(key, node):
    """ node transformation that unrolls the typed elements
        { "bool": { "partialResults": "true",  }, .. } --> { partialResults : true, .. }
    """

    if not isinstance(node, dict):
        # because I am not sure how to move up list elements, which are essentially 
        # anonymous values.
        return None

    caster=solr_type_to_caster.get(key)
    if caster:
        return [ ( k, caster(v) )  for k,v in unxml.node_children_items(node) ]

if __name__=='__main__':
    import sys
    unxml.dump_json(sys.argv[1], nt_solr_untype)
