import Link from 'next/link';

export default function Home() {
  return <section><h1>Disclosures built into publishing.</h1>
    <p>A short fictional article demonstrates a notice included in the first HTML response and retained during client navigation.</p>
    <Link href="/news/">Read the example article</Link>
  </section>;
}
