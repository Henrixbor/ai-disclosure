'use strict';
const replies = {
  labels: 'Not all AI involvement triggers the same disclosure duty. Establish the asset’s origin, purpose and legal context. Unknown is a question to resolve, not evidence that something is human-made.',
  popup: 'A site statement can provide extra context. It should not replace a required, clear disclosure with the relevant content or interaction. This demo keeps those notices visible.',
  future: 'Connect disclosure checks to your publishing workflow. Record facts at creation, tie reviews to revisions, and hold unresolved changes before publishing. Installing a skill alone does not monitor your site.'
};
const log = document.querySelector('#chat-log');
document.querySelectorAll('[data-chat]').forEach(button => button.addEventListener('click', () => {
  const question = document.createElement('p'); question.className = 'bubble user'; question.textContent = button.textContent;
  const answer = document.createElement('p'); answer.className = 'bubble'; answer.textContent = replies[button.dataset.chat];
  log.append(question, answer); log.scrollTop = log.scrollHeight;
}));
document.querySelector('.reset-chat').addEventListener('click', () => {
  log.replaceChildren(); const greeting = document.createElement('p'); greeting.className='bubble'; greeting.textContent='Choose a question to see how the notice stays with the conversation.'; log.append(greeting);
});
const imageDialog = document.querySelector('#image-dialog');
document.querySelector('.image-open').addEventListener('click', () => imageDialog.showModal());
document.querySelector('#open-site-notice').addEventListener('click', () => document.querySelector('#site-dialog').showModal());
document.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
document.querySelectorAll('[data-publish]').forEach(button => button.addEventListener('click', async () => {
  const status = document.querySelector('#publish-status');
  const buttons = [...document.querySelectorAll('[data-publish]')]; buttons.forEach(b=>b.disabled=true);
  try {
    const response = await fetch('publishing-demo.json'); if (!response.ok) throw new Error('Unable to load');
    const results = await response.json(); const result = results[button.dataset.publish];
    if (result.html === null) { status.textContent='Update held: the evidence belongs to an older revision. The published version stays unchanged.'; }
    else { document.querySelector('#publication').innerHTML=result.html; status.textContent='Recorded update rendered. This precomputed example passed the local renderer’s revision check.'; }
  } catch { status.textContent='The example could not load. The published version is unchanged. Try again while connected to this site.'; }
  finally { buttons.forEach(b=>b.disabled=false); }
}));
