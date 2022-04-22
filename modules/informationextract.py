from collections import OrderedDict
from modloader.modast import find_label, ASTHook
import renpy
from renpy import ast

def name_node(node):
    if not node:
        return ''
    elif isinstance(node, ASTHook):
        return (node.filename, node.linenumber, 'ASTHook', node.name)
    elif isinstance(node, ast.Label):
        return (node.filename, node.linenumber, 'label', node.name)
    elif isinstance(node, (ast.Scene,ast.Show,ast.Hide)):
        typename = {ast.Scene: 'scene', ast.Show: 'show', ast.Hide: 'hide'}[type(node)]
        return (node.filename, node.linenumber, typename, ' '.join(node.imspec[0]))
    elif isinstance(node, (ast.Define, ast.Default, ast.Python, ast.TranslatePython)):
        typename = {ast.Define: 'define', ast.Default: 'default', ast.Python: 'python', ast.TranslatePython: 'TranslatePython'}[type(node)]
        if hasattr(node, 'store'):
            return (node.filename, node.linenumber, typename, node.store, node.code.source)
        else:
            return (node.filename, node.linenumber, typename, node.code.source)
    elif isinstance(node, ast.Say):
        return (node.filename, node.linenumber, 'say', node.who, node.what)
    elif isinstance(node, ast.With):
        return (node.filename, node.linenumber, 'with', unicode(node.expr))
    elif isinstance(node, ast.Call):
        return (node.filename, node.linenumber, 'call', unicode(node.label))
    elif isinstance(node, ast.Jump):
        return (node.filename, node.linenumber, 'jump', unicode(node.target))
    else:
        return (node.filename, node.linenumber, type(node).__name__)


def get_children(node):
    children = OrderedDict()
    if isinstance(node, ASTHook):
        if node.next:
            children[name_node(node.next)] = node.next
        if node.old_next:
            children[name_node(node.old_next)] = node.old_next
    elif isinstance(node, ast.If):
        for entry in node.entries:
            if entry[0] != 'False' and entry[1]:
                children[name_node(entry[1][0])] = entry[1][0]
    elif isinstance(node, ast.Menu):
        for entry in node.items:
            if entry[1] != 'False' and entry[2]:
                children[name_node(entry[2][0])] = entry[2][0]
    elif isinstance(node, ast.Jump):
        if node.expression:
            print("ERROR: Jump with expression")
        else:
            children[node.target] = find_label(node.target)
    elif isinstance(node, ast.Call):
        if node.expression:
            print("ERROR: Call with expression")
        else:
            children[node.label] = find_label(node.label)
        if node.next:
            children[name_node(node.next)] = node.next
    else:
        if node.next:
            children[name_node(node.next)] = node.next

    return children



def read_game_tree():
    start = find_label('begingame')

    node_queue = [start]
    game_tree = OrderedDict()
    while node_queue:
        node = node_queue.pop()
        if name_node(node) not in game_tree:
            children = get_children(node)
            game_tree[name_node(node)] = list(children.keys())
            node_queue.extend(children.values())
        else:
            pass # Already processed

    return game_tree


def save_game_tree_to_file(f):
    game_tree = read_game_tree()
    f.write('\ntree={\n')
    for node, children in game_tree.items():
        f.write('%r:[\n'%(node,))
        for child in children:
            f.write('\t%r,\n'%(child,))
        f.write('],\n')
    f.write('}\n')


def save_file_list_to_file(f):
    # Index the archives, if we haven't already.
    renpy.loader.index_archives()

    files = list(filename for _,filename in renpy.loader.game_files if not filename.startswith('mods/'))

    f.write('\ngame_files=[\n')
    for filename in files:
        f.write('\t%r,\n'%(filename,))
    f.write(']\n')


def save_imagespec_list_to_file(f):
    f.write('\nimages=[\n')
    for name in renpy.display.image.images.keys():
        f.write('\t%r,\n'%(name,))
    f.write(']\n')



def run():
    with open('game/mods/infoextract/game_tree.py','w') as f:
        save_file_list_to_file(f)
        save_imagespec_list_to_file(f)
        save_game_tree_to_file(f)