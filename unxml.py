#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Read XML into object hierarchey, like perl's XML::Simple
"""
import xml.sax.handler

special_key_prefix=set(['_', ':'])
PARENT_KEY='_parent'
TEXT_KEY='_text'

def is_special_key(key):
    return key[0] in special_key_prefix

def delkey(d,k):
    """ delete key as an expression """
    if d.has_key(k):
        del d[k]

def node_children_items(node):
    """ node --> key-value pairs where key includes list index. """
    if isinstance(node, basestring):
        return []
    if isinstance(node, list):
        return enumerate(node)
    if isinstance(node, dict):
        return [ (k,v)
                 for k,v in node.items() 
                 if not is_special_key(k) 
                 ]
    assert False, type(node)

def node_children(node):
    """ node --> children """
    return sum([ v if isinstance(v, list) else [v]
                 for k,v in node_children_items(node) ],
               [])

def node_add_child(node, tag, attrs, attr_key=None):
    """ adds a new node to the node and returns the newly added node """

    if not attr_key:
        attr_key=lambda x: x

    child={ PARENT_KEY : node }
    for k,v in attrs.items():
        child[attr_key(k)]=v          # xx attr key prefix

    node.setdefault(tag, []).append(child)
    return child

#### node_map
class WrongMapResultType(Exception):
    # todo add instructions
    pass

def node_map1(node, map_node=lambda n: None):
    """ Recursively edit or replace nodes.
        map_node: node -> node | None
        map_node gets to edit the node.
        If truthy value is returned, it must be a new node. 
        In this case, the original node is replaced by it.
    """
    for k,c in node_children_items(node):
        replacement=map_node(c)
        if replacement:
            node[k]=replacement
        node_map1(c, map_node=map_node)

def node_map2(node, map_key_node=lambda k,n: None):
    """ Recursively edit or replace nodes and their keys.
        Can do what node_map1 does with nodes, plus this version can
        "rename" the nodes.
        map_key_node takes key and node and could return one of 3 things:
        * None (or any falsy value): the node should be left alone
        * key-node pair:             the current key-node is replaced by the returned pair
        * list of key-node pairs:    expands the current key-node to the returned items.

    """
    for cur_key,cur_node in node_children_items(node):

        result=map_key_node(cur_key,cur_node)

        # resolve the result
        # take either a 2-tuple or a list of 2-tuples
        if not result:
            # no change requested
            items=[]
        elif isinstance(result, tuple):
            # a single <key,node> replacement
            assert len(result)==2
            items=[result]
        elif isinstance(result, list):
            # expanding a node to multiple items.
            items=result
        else:
            raise WrongMapResultType(result)

        # node.update(dict(items)), but for list as well.
        for item in items:
            rkey,rnode=item
            node[rkey]=rnode

        # if mapping was request and the key is not among the newly added, delete it.
        if items:
            if cur_key not in [kk for kk,v in items ]:
                del node[cur_key]

        node_map2(cur_node, map_key_node=map_key_node)

    return node

_argcnt_to_mapper={ 1:node_map1, 2:node_map2 }

def node_map(node, transform_node):
    """ recursively transform nodes.
        see node_map1 and node_map2 for transform_node signiture.
    """
    from inspect import getargspec
    mapper=_argcnt_to_mapper[len(getargspec(transform_node).args)]
    return mapper(node, transform_node)
####

def transform(node, *nts):
    """ apply a number of node transformations """
    for nt in nts:
        node_map(node, nt)
    return node

#### standard node transformations that are applied by default.

def nt_unlink_parent(n):
    """ unlink _parent """
    if isinstance(n, dict):
        delkey(n, PARENT_KEY) 

def nt_unwrap_text(n):
    """ unwrap text node: [{ _text="foo" }, { _text="bar" } ] --> [ "foo", "bar" ] """
    return n[TEXT_KEY] if isinstance(n, dict) and set(n.keys())==set([TEXT_KEY]) else None

def nt_unwrap_singletons(n):
    """ unwrap singletons """
    return n[0] if isinstance(n, list) and len(n)==1 else None

def nt_annotate_assoc(n):
    """ annotate assoc nodes
        * <str name="foo">bar</str>    ===>    "foo": "bar", 
        * <str name="foo"/>            ===>    "foo": "",
    """
    if isinstance(n, dict) and (set(n.keys())==set([":name", TEXT_KEY]) or  set(n.keys())==set([":name"])):
        return { '_assoc' : True, '_k' : n[":name"], '_v' : n.get(TEXT_KEY, '') }

def nt_flatten_alist(n):
    """ flatten alist [ { name="foo" val="bar" }, .. ]  ---> { foo=>"bar", .. } """
    if isinstance(n, list) and set([ c.get('_assoc') for c in n ])==set([True]):
        return dict([(a.get('_k'),a.get('_v')) for a in n ])

standard_transformations=[
    nt_unlink_parent,
    nt_annotate_assoc,
    nt_flatten_alist,
    nt_unwrap_text,
    nt_unwrap_singletons,
    ]

####
class Parser(xml.sax.handler.ContentHandler):
    """ sax handler to parse xml into object hierarchey """

    def __init__(self, attr_key=None):
        self.cur={}
        self.root=self.cur
        self.attr_key=attr_key

    def startElement(self, name, attrs):
        self.cur=node_add_child(self.cur, name, attrs, attr_key=self.attr_key)

    def endElement(self, name):
        self.cur=self.cur[PARENT_KEY]
        if self.cur.get(PARENT_KEY) is None:
            self.done()

    def characters(self, content):
        s=content.strip()
        if s:
            self.cur[TEXT_KEY]=self.cur.setdefault(TEXT_KEY, '')+s

    def done(self):
        """ completion hook """
        pass

def _parse(xmlstr, *transformers, **opts):
    """ parse xml into a raw object hierarchey. """
    parser=Parser(**opts)
    xml.sax.parseString(xmlstr, parser)
    transform(parser.root, *transformers)
    return parser.root

def parse(xmlstr, *transformers, **opts):
    """ parse xml into a nice object hierarchey """
    return _parse(xmlstr, *(standard_transformations + list(transformers)), **opts)

def dump_json(xml_file, *transformers, **opts):
    """ a sample main that takes a path to an xml file and dumps it as json """
    import sys
    import json

    # dwim arg
    if xml_file=='-':
        xml_file=sys.stdin
    if isinstance(xml_file, basestring):
        xml_file=file(xml_file)

    xmlo=parse(xml_file.read(), *transformers, **opts)
    print json.dumps(xmlo, indent=4)

def find_nodes(node, pred):
    """ find the nodes matching the predicate """
    if pred(node):
        return [node]
    return sum([ node_find(c, pred) for c in unxml.node_children(node) ], [])

if __name__=='__main__':

    import sys

    try:
        xml_file=sys.argv[1]
    except IndexError:
        print >>sys.stderr, "usage %s [xml_file|-]" % sys.argv[0]
        sys.exit(1)
    dump_json(xml_file, attr_key=lambda x: x)

# xx how to filter and selectively export?
__all__=set(dir()).difference(['Parser'])

