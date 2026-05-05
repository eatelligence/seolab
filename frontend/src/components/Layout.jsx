import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export function Layout() {
  return (
    <div className="flex h-screen bg-ink-400 text-bone">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-[1480px] mx-auto px-8 py-10">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
