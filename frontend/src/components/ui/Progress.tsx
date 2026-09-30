import React from 'react';
export function Progress({ value, ...props }: any) { return <div {...props}><div style={{width: value + '%'}}></div></div>; }
