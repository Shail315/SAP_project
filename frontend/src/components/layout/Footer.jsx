function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white/70">
      <div className="mx-auto flex w-full max-w-7xl flex-col justify-between gap-2 px-4 py-6 text-sm text-slate-500 md:flex-row md:px-8">
        <p>MetaFuse - AI metadata for YouTube creators</p>
        <div className="flex gap-4">
          <a href="https://github.com" target="_blank" rel="noreferrer">GitHub</a>
          <a href="#">About</a>
          <a href="#">Contact</a>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
