import Card from "../ui/Card";

function Sidebar({ items, selectedId, onSelect }) {
  return (
    <aside className="w-full max-w-xs">
      <Card title="History">
        <ul className="space-y-2">
          {items.length === 0 ? (
            <li className="rounded-xl bg-slate-50 p-3 text-sm text-slate-500">
              No uploads yet.
            </li>
          ) : (
            items.map((item) => (
              <li key={item.id}>
                <button
                  onClick={() => onSelect(item.id)}
                  className={`w-full rounded-xl border px-3 py-2 text-left text-sm transition ${
                    selectedId === item.id
                      ? "border-brand-300 bg-brand-50 text-brand-700"
                      : "border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  <p className="truncate font-semibold">{item.filename}</p>
                  <p className="mt-1 text-xs text-slate-500">{item.title || "Untitled"}</p>
                </button>
              </li>
            ))
          )}
        </ul>
      </Card>
    </aside>
  );
}

export default Sidebar;
