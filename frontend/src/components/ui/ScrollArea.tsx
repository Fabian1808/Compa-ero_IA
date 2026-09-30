import React from 'react';
export function ScrollArea({ children, ...props }: any) { return <div style={{overflow: 'auto'}} {...props}>{children}</div>; }
