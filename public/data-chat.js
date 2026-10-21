/* Preset answers for the supplied 12-order assessment snapshot. No model or chat API. */
const guidedQuestions = [
  [
    "How much revenue was delivered?",
    "Delivered line revenue totals $9,994.624060 before display rounding, or $9,994.62. Shipping is excluded.",
    "fact_sales · SUM(line_revenue_usd), Delivered only"
  ],
  [
    "How many orders and items are in the data?",
    "The source contains 12 orders and 20 line items. All 20 lines are retained in fact_sales.",
    "Source JSON · orders and line_items counts"
  ],
  [
    "Which order statuses are included?",
    "There are 9 Delivered orders, 1 Returned, 1 Cancelled and 1 Processing. Revenue reports include only Delivered; the other records remain available for audit.",
    "Source JSON · order status counts"
  ],
  [
    "What is the average delivered order value?",
    "Average delivered order value is $1,110.51: unrounded delivered revenue of $9,994.624060 divided by 9 distinct delivered orders.",
    "fact_sales · delivered revenue / distinct delivered orders"
  ],
  [
    "Which month generated the most revenue?",
    "March 2024 leads with $3,046.35 in delivered revenue. July follows with $2,249.93.",
    "Q1 · monthly delivered revenue"
  ],
  [
    "Which product generates the most revenue?",
    "Office Chair Ergonomic leads with $4,709.84, accounting for 47.12% of delivered revenue.",
    "Q2 · product revenue and share"
  ],
  [
    "Who is the highest-revenue customer?",
    "Daniel Rosenthal ranks first with $3,269.89 from 2 delivered orders. Marco Ferrari ranks second with $2,915.87.",
    "Q4 · customer revenue rank"
  ],
  [
    "Which segment and channel combination leads?",
    "Business customers through the Partner channel generate $5,165.80, the largest segment/channel combination.",
    "Q3 · segment and channel"
  ],
  [
    "What changed for Sarah Mitchell?",
    "Sarah changes from Premium to VIP in ORD-2024-012. Her earlier orders retain Premium attribution. Across her 3 delivered orders, revenue is $839.92.",
    "dim_customer historical versions · Q4 customer totals"
  ],
  [
    "How are discounts and EUR sales handled?",
    "Each line uses quantity × unit price × (1 − discount / 100). EUR revenue is multiplied by 1.08; USD uses 1.00. A missing or NULL discount defaults to zero. The source contains no NULL discounts.",
    "src/pipeline.py · revenue and FX rules"
  ]
];
const launcher = document.querySelector('#data-chat-launcher');
const dialog = document.querySelector('#data-chat');
const questions = document.querySelector('#data-chat-questions');
const messages = document.querySelector('#data-chat-messages');
let previousFocus;
guidedQuestions.forEach(([question, answer, source]) => {
 const button = document.createElement('button');
 button.type = 'button'; button.textContent = question;
 button.addEventListener('click', () => {
  messages.replaceChildren();
  const asked = document.createElement('p'); asked.className = 'chat-question'; asked.textContent = question;
  const reply = document.createElement('p'); reply.className = 'chat-answer'; reply.textContent = answer;
  const evidence = document.createElement('small'); evidence.textContent = 'Source: ' + source;
  messages.append(asked, reply, evidence);
 });
 questions.append(button);
});
launcher.addEventListener('click', () => {
 previousFocus = document.activeElement;
 dialog.showModal();
 launcher.setAttribute('aria-expanded', 'true');
});
function closeDataChat() {
 dialog.close();
 launcher.setAttribute('aria-expanded', 'false');
 if (previousFocus) previousFocus.focus();
}
document.querySelector('#data-chat-close').addEventListener('click', closeDataChat);
dialog.addEventListener('cancel', event => { event.preventDefault(); closeDataChat(); });
dialog.addEventListener('click', event => { if (event.target === dialog) {
 const rect = dialog.getBoundingClientRect();
 if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) closeDataChat();
}});
