import React from 'react';
export function Dialog({ children, ...props }: any) { return <div {...props}>{children}</div>; }
export function DialogTrigger({ children, ...props }: any) { return <button {...props}>{children}</button>; }
export function DialogContent({ children, ...props }: any) { return <div {...props}>{children}</div>; }
export function DialogHeader({ children, ...props }: any) { return <div {...props}>{children}</div>; }
export function DialogTitle({ children, ...props }: any) { return <h2 {...props}>{children}</h2>; }
export function DialogDescription({ children, ...props }: any) { return <p {...props}>{children}</p>; }
