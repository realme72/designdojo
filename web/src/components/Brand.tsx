export default function Brand() {
  return (
    <a className="brand" href="#/" title="All problems">
      <svg className="brand-mark" viewBox="0 0 32 32" aria-hidden="true">
        <rect width="32" height="32" rx="7" fill="var(--accent)" />
        <path d="M8 9h7v7H8zM17 16h7v7h-7z" fill="var(--panel)" />
        <path d="M15 12.5h4.5V16" stroke="var(--panel)" strokeWidth="2" fill="none" />
      </svg>
      Joinery
    </a>
  )
}
