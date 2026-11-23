import type { GroupPerm } from "../types";
import { PERM_LABEL } from "../utils/format";

const ALL: GroupPerm[] = ["create", "update", "stock"];

interface Props {
  value: GroupPerm[];
  onChange: (value: GroupPerm[]) => void;
  disabled?: boolean;
}

// গ্রুপ-সদস্যের অনুমতি বাছাইয়ের চেকবক্স
export default function PermChecks({ value, onChange, disabled }: Props) {
  return (
    <span className="perms">
      {ALL.map((p) => (
        <label key={p} className="perm">
          <input
            type="checkbox"
            disabled={disabled}
            checked={value.includes(p)}
            onChange={(e) => onChange(e.target.checked ? [...value, p] : value.filter((x) => x !== p))}
          />
          {PERM_LABEL[p]}
        </label>
      ))}
    </span>
  );
}
