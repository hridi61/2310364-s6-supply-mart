interface AlertProps {
  kind: "success" | "error";
  children: string;
}

export default function Alert({ kind, children }: AlertProps) {
  return (
    <div className={`alert alert-${kind}`} role={kind === "error" ? "alert" : "status"}>
      {children}
    </div>
  );
}