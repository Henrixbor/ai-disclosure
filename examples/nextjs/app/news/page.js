import article from '../../.generated/article.json';

export default function News() {
  // Only trusted repository HTML passes through the renderer. It is not a sanitizer.
  return <div dangerouslySetInnerHTML={{ __html: article.html }} />;
}
