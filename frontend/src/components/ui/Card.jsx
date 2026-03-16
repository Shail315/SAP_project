function Card({ title, action, children, className = "" }) {
  return (
    <section className={`panel-card p-5 ${className}`}>
      {(title || action) && (
        <div className="mb-4 flex items-start justify-between gap-3">
          <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

export default Card;
