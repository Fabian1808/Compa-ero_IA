import React from 'react';
export function Switch({ checked, onCheckedChange, ...props }: any) { 
  return <input type="checkbox" checked={checked} onChange={(e) => onCheckedChange && onCheckedChange(e.target.checked)} {...props} />; 
}
