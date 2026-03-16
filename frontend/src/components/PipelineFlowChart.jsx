import { useState, useEffect } from 'react';

const NODES = [
  { id: 'start', label: '__start__', desc: 'Query input', x: 400, y: 30, type: 'terminal' },
  { id: 'query', label: 'query_node', desc: 'Validate & init state', x: 400, y: 110, type: 'node' },
  { id: 'route', label: 'route_query', desc: 'Simple vs complex?', x: 400, y: 190, type: 'decision' },
  { id: 'rewrite', label: 'rewrite_node', desc: 'Multi-query + HyDE', x: 400, y: 280, type: 'node' },
  { id: 'retrieve', label: 'retrieve_node', desc: 'Hybrid vector + BM25', x: 400, y: 370, type: 'node' },
  { id: 'rerank', label: 'rerank_node', desc: 'Cross-encoder rerank', x: 400, y: 460, type: 'node' },
  { id: 'generate', label: 'generate_node', desc: 'LLM answer generation', x: 400, y: 550, type: 'node' },
  { id: 'evaluate', label: 'evaluate_node', desc: 'Quality & faithfulness', x: 400, y: 640, type: 'decision' },
  { id: 'retry', label: 'retry_node', desc: 'Backoff & retry', x: 180, y: 640, type: 'retry' },
  { id: 'end', label: '__end__', desc: 'Return answer', x: 400, y: 740, type: 'terminal' },
];

const EDGES = [
  { from: 'start', to: 'query', type: 'solid' },
  { from: 'query', to: 'route', type: 'solid' },
  { from: 'route', to: 'rewrite', type: 'solid', label: 'complex' },
  { from: 'route', to: 'generate', type: 'dashed', label: 'simple', offsetX: 160 },
  { from: 'rewrite', to: 'retrieve', type: 'solid' },
  { from: 'retrieve', to: 'rerank', type: 'solid' },
  { from: 'rerank', to: 'generate', type: 'solid' },
  { from: 'generate', to: 'evaluate', type: 'solid' },
  { from: 'evaluate', to: 'end', type: 'solid', label: 'pass' },
  { from: 'evaluate', to: 'retry', type: 'dashed', label: 'fail' },
  { from: 'retry', to: 'rewrite', type: 'dashed', label: 'retry' },
];

const NODE_COLORS = {
  terminal: { bg: '#e8e4ff', border: '#8b7cf7', text: '#4c3fb0' },
  node: { bg: '#f0edff', border: '#a89cf7', text: '#4c3fb0' },
  decision: { bg: '#fff3e0', border: '#ff9800', text: '#e65100' },
  retry: { bg: '#fff8e1', border: '#ffc107', text: '#f57f17' },
};

function getNodeCenter(node) {
  const w = node.type === 'terminal' ? 120 : 160;
  const h = node.type === 'terminal' ? 40 : 60;
  return { cx: node.x, cy: node.y + h / 2 };
}

function NodeBox({ node, pulseDelay }) {
  const colors = NODE_COLORS[node.type] || NODE_COLORS.node;
  const isTerminal = node.type === 'terminal';
  const w = isTerminal ? 120 : 160;
  const h = isTerminal ? 40 : 60;
  const rx = isTerminal ? 20 : 10;

  return (
    <g style={{ cursor: 'pointer' }}>
      {/* Pulse glow */}
      <rect
        x={node.x - w / 2 - 4}
        y={node.y - 4}
        width={w + 8}
        height={h + 8}
        rx={rx + 4}
        fill="none"
        stroke={colors.border}
        strokeWidth="2"
        opacity="0.4"
      >
        <animate
          attributeName="opacity"
          values="0.15;0.5;0.15"
          dur="2.5s"
          begin={`${pulseDelay}s`}
          repeatCount="indefinite"
        />
        <animate
          attributeName="stroke-width"
          values="2;5;2"
          dur="2.5s"
          begin={`${pulseDelay}s`}
          repeatCount="indefinite"
        />
      </rect>

      {/* Main box */}
      <rect
        x={node.x - w / 2}
        y={node.y}
        width={w}
        height={h}
        rx={rx}
        fill={colors.bg}
        stroke={colors.border}
        strokeWidth="2"
      />

      {/* Label */}
      <text
        x={node.x}
        y={node.y + (isTerminal ? 16 : 20)}
        textAnchor="middle"
        fill={colors.text}
        fontSize="12"
        fontWeight="bold"
        fontFamily="Inter, system-ui, sans-serif"
      >
        {node.label}
      </text>

      {/* Description */}
      {!isTerminal && (
        <text
          x={node.x}
          y={node.y + 40}
          textAnchor="middle"
          fill="#888"
          fontSize="10"
          fontFamily="Inter, system-ui, sans-serif"
        >
          {node.desc}
        </text>
      )}
    </g>
  );
}

function EdgeLine({ edge, nodes }) {
  const fromNode = nodes.find(n => n.id === edge.from);
  const toNode = nodes.find(n => n.id === edge.to);
  if (!fromNode || !toNode) return null;

  const from = getNodeCenter(fromNode);
  const to = getNodeCenter(toNode);

  const isDashed = edge.type === 'dashed';

  // Special path for simple route (curve right)
  if (edge.offsetX) {
    const midX = from.cx + edge.offsetX;
    const path = `M ${from.cx} ${from.cy} C ${midX} ${from.cy}, ${midX} ${to.cy}, ${to.cx + 80} ${to.cy}`;
    return (
      <g>
        <path
          d={path}
          fill="none"
          stroke={isDashed ? '#ff9800' : '#a89cf7'}
          strokeWidth="2"
          strokeDasharray={isDashed ? '6,4' : 'none'}
          markerEnd="url(#arrowhead)"
        />
        {edge.label && (
          <text
            x={midX - 10}
            y={(from.cy + to.cy) / 2}
            fill="#ff9800"
            fontSize="10"
            fontWeight="600"
            fontFamily="Inter, system-ui, sans-serif"
          >
            {edge.label}
          </text>
        )}
        <circle r="3" fill="#ff9800">
          <animateMotion dur="3s" repeatCount="indefinite" path={path} />
        </circle>
      </g>
    );
  }

  // Special path for retry (horizontal + curve back up)
  if (edge.from === 'retry' && edge.to === 'rewrite') {
    const path = `M ${from.cx} ${from.cy - 10} C ${from.cx - 60} ${from.cy - 80}, ${to.cx - 100} ${to.cy}, ${to.cx - 80} ${to.cy}`;
    return (
      <g>
        <path
          d={path}
          fill="none"
          stroke="#ffc107"
          strokeWidth="2"
          strokeDasharray="6,4"
          markerEnd="url(#arrowhead-amber)"
        />
        {edge.label && (
          <text x={from.cx - 80} y={(from.cy + to.cy) / 2 - 10} fill="#f57f17" fontSize="10" fontWeight="600" fontFamily="Inter, system-ui, sans-serif">
            {edge.label}
          </text>
        )}
        <circle r="3" fill="#ffc107">
          <animateMotion dur="3.5s" repeatCount="indefinite" path={path} />
        </circle>
      </g>
    );
  }

  // Horizontal for evaluate → retry
  if (edge.from === 'evaluate' && edge.to === 'retry') {
    const fCenter = getNodeCenter(fromNode);
    const tCenter = getNodeCenter(toNode);
    const path = `M ${fCenter.cx - 80} ${fCenter.cy} L ${tCenter.cx + 80} ${tCenter.cy}`;
    return (
      <g>
        <path d={path} fill="none" stroke="#ffc107" strokeWidth="2" strokeDasharray="6,4" markerEnd="url(#arrowhead-amber)" />
        {edge.label && (
          <text x={(fCenter.cx + tCenter.cx) / 2} y={fCenter.cy - 8} textAnchor="middle" fill="#f57f17" fontSize="10" fontWeight="600" fontFamily="Inter, system-ui, sans-serif">
            {edge.label}
          </text>
        )}
        <circle r="3" fill="#ffc107">
          <animateMotion dur="2s" repeatCount="indefinite" path={path} />
        </circle>
      </g>
    );
  }

  // Default: straight vertical line
  const fromH = fromNode.type === 'terminal' ? 40 : 60;
  const x1 = from.cx;
  const y1 = fromNode.y + fromH;
  const x2 = to.cx;
  const y2 = toNode.y;
  const path = `M ${x1} ${y1} L ${x2} ${y2}`;

  return (
    <g>
      <line
        x1={x1} y1={y1} x2={x2} y2={y2}
        stroke={isDashed ? '#ff9800' : '#a89cf7'}
        strokeWidth="2"
        strokeDasharray={isDashed ? '6,4' : 'none'}
        markerEnd={isDashed ? 'url(#arrowhead-orange)' : 'url(#arrowhead)'}
      />
      {edge.label && (
        <text
          x={(x1 + x2) / 2 + 12}
          y={(y1 + y2) / 2}
          fill={isDashed ? '#ff9800' : '#7c6cf0'}
          fontSize="10"
          fontWeight="600"
          fontFamily="Inter, system-ui, sans-serif"
        >
          {edge.label}
        </text>
      )}
      <circle r="3" fill={isDashed ? '#ff9800' : '#8b7cf7'}>
        <animateMotion dur="2s" repeatCount="indefinite" path={path} />
      </circle>
    </g>
  );
}

export default function PipelineFlowChart() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 100);
    return () => clearTimeout(t);
  }, []);

  return (
    <div
      className="w-full flex justify-center"
      style={{
        opacity: visible ? 1 : 0,
        transition: 'opacity 0.8s ease-in',
      }}
    >
      <svg viewBox="0 0 800 800" width="100%" height="auto" style={{ maxWidth: 700 }}>
        <defs>
          <marker id="arrowhead" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 Z" fill="#a89cf7" />
          </marker>
          <marker id="arrowhead-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 Z" fill="#ff9800" />
          </marker>
          <marker id="arrowhead-amber" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 Z" fill="#ffc107" />
          </marker>
        </defs>

        {/* Edges */}
        {EDGES.map((edge, i) => (
          <EdgeLine key={i} edge={edge} nodes={NODES} />
        ))}

        {/* Nodes */}
        {NODES.map((node, i) => (
          <NodeBox key={node.id} node={node} pulseDelay={i * 0.3} />
        ))}
      </svg>
    </div>
  );
}
