import { Header } from "@/components/Header";
import { AuthenticatedShell } from "@/components/AuthProvider";

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthenticatedShell>
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex-1">{children}</main>
      </div>
    </AuthenticatedShell>
  );
}
