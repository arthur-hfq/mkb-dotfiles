#!/usr/bin/env python3
import sys, json, subprocess

def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode('utf-8')

def find_focused_node(node):
    if not node.get('nodes') and not node.get('floating_nodes'):
        return node.get('name', '')
    
    if node.get('focus'):
        focused_id = node['focus'][0]
        for child in node.get('nodes', []) + node.get('floating_nodes', []):
            if child['id'] == focused_id:
                return find_focused_node(child)
    return ""

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    
    target_monitor = sys.argv[1]
    
    try:
        workspaces = json.loads(run("i3-msg -t get_workspaces"))
        visible_ws = None
        for w in workspaces:
            if w['output'] == target_monitor and w['visible']:
                visible_ws = w['name']
                break
        
        if not visible_ws:
            print("")
            sys.exit(0)
            
        tree = json.loads(run("i3-msg -t get_tree"))
        
        def search_ws(node):
            if node.get('type') == 'workspace' and node.get('name') == visible_ws:
                return node
            for child in node.get('nodes', []) + node.get('floating_nodes', []):
                res = search_ws(child)
                if res: return res
            return None
            
        ws_node = search_ws(tree)
        if ws_node:
            title = find_focused_node(ws_node)
            print(title[:45] + ("..." if len(title) > 45 else ""))
        else:
            print("")
            
    except:
        print("")

if __name__ == "__main__":
    main()
