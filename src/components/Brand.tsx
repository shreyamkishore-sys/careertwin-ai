import type { MouseEventHandler } from "react";

interface BrandProps {
  onClick?: MouseEventHandler<HTMLAnchorElement>;
}

export function Brand({ onClick }: BrandProps) {
  return (
    <a className="brand" href="#" aria-label="CareerTwin AI home" onClick={onClick}>
      <span className="brand-mark" aria-hidden="true">
        <span />
        <span />
        <span />
        <span />
      </span>
      <span>career<span className="brand-light">twin</span></span>
      <span className="brand-ai">AI</span>
    </a>
  );
}
