import Link from 'next/link';
import '../.generated/disclosure.css';
import './style.css';

export const metadata = { title: 'AI Disclosure · Next.js example', robots: { index: false, follow: false } };

export default function Layout({ children }) {
  return <html lang="en"><body>
    <header><Link href="/">AI Disclosure example</Link><span>Fictional publication</span></header>
    <main>{children}</main>
    <footer>A local integration example. No model service or visitor tracking.</footer>
  </body></html>;
}
