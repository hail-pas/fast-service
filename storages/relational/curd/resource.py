from typing import List, Optional

from storages.relational.models import System
from storages.relational.models.account import Role
from storages.relational.pydantic.resource import (
    ResourceLevelTreeNode,
    ResourceLevelTreeBaseNode,
)


def resource_list_to_tree(nodes: list) -> List[ResourceLevelTreeNode]:
    node_dict = {
        node.id: ResourceLevelTreeNode(
            **ResourceLevelTreeBaseNode.from_orm(node).dict(), children=[]
        )
        for node in nodes
    }
    tree_list = []
    for node in node_dict.values():
        if node.parent_id is None:
            tree_list.append(node)
        else:
            node_dict[node.parent_id].children.append(node)
            node_dict[node.parent_id].children.sort(key=lambda x: x.order_num)
    tree_list.sort(key=lambda x: x.order_num)
    return tree_list


async def get_resource_tree(
    system: System, role: Optional[Role]
) -> List[ResourceLevelTreeNode]:
    if role is None:
        # 获取系统的所有资源
        available_resource_nodes = await system.resources.all()
    else:
        # 获取角色在系统中可用的资源
        available_resource_nodes = await role.resources.filter(systems=system)
    return resource_list_to_tree(available_resource_nodes)
