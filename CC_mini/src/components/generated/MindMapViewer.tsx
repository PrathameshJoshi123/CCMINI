import React, { useMemo } from 'react';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';
import { MindMapData } from '@/types';

interface MindMapViewerProps {
  data: MindMapData;
}

export const MindMapViewer: React.FC<MindMapViewerProps> = ({ data }) => {
  // Calculate tree layout positions
  const { nodes, edges } = useMemo(() => {
    const levelWidth = 300; // Horizontal spacing between levels
    const nodeHeight = 100; // Vertical spacing between nodes
    const levelCounts: Map<number, number> = new Map();

    // Calculate level for each node and count nodes per level
    const nodeMap = new Map(data.nodes.map((n) => [n.id, n]));
    const levelMap = new Map<string, number>();

    // Assign levels using BFS
    const queue = data.nodes.filter((n) => !n.parent);
    queue.forEach((n) => levelMap.set(n.id, 0));

    let currentLevel = 0;
    while (queue.length > 0) {
      const levelSize = queue.length;
      const count = levelCounts.get(currentLevel) || 0;
      levelCounts.set(currentLevel, count + levelSize);

      for (let i = 0; i < levelSize; i++) {
        const node = queue.shift()!;
        const children = data.nodes.filter((n) => n.parent === node.id);
        children.forEach((child) => {
          levelMap.set(child.id, currentLevel + 1);
          queue.push(child);
        });
      }
      currentLevel++;
    }

    // Calculate positions for each node
    const levelPositions = new Map<number, number>();
    const processedNodes = data.nodes.map((node) => {
      const level = levelMap.get(node.id) || 0;
      const positionInLevel = levelPositions.get(level) || 0;
      levelPositions.set(level, positionInLevel + 1);

      const totalAtLevel = data.nodes.filter((n) => (levelMap.get(n.id) || 0) === level).length;
      const verticalOffset = (positionInLevel - (totalAtLevel - 1) / 2) * nodeHeight;

      return {
        id: node.id,
        data: { label: node.label },
        position: {
          x: level * levelWidth,
          y: verticalOffset + 300, // Center vertically
        },
        style: {
          background: level === 0 ? '#1e40af' : level === 1 ? '#3b82f6' : '#60a5fa',
          color: 'white',
          padding: '12px 20px',
          borderRadius: '8px',
          fontSize: level === 0 ? '16px' : '14px',
          fontWeight: level === 0 ? 600 : 500,
          border: '2px solid #1e3a8a',
          minWidth: '150px',
          textAlign: 'center',
        },
      };
    });

    const processedEdges = data.edges.map((edge) => ({
      id: `${edge.from}-${edge.to}`,
      source: edge.from,
      target: edge.to,
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#6366f1', strokeWidth: 2 },
    }));

    return { nodes: processedNodes, edges: processedEdges };
  }, [data]);

  return (
    <div className="h-[600px] bg-gray-50 rounded-lg border border-gray-200">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        attributionPosition="bottom-right"
        minZoom={0.1}
        maxZoom={1.5}
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
};
