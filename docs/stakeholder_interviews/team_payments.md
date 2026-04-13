# Stakeholder Interview: Payments & Risk Team

**Date:** Monday, 2:00 PM
**Interviewee:** Andres Ramirez, Head of Payments & Risk
**Location:** Meeting Room "El Dorado", Emporyum Tech HQ Bogota
**Attendees:** Andres (Payments), You (AI Team)

---

## Transcript

**You:** Andres, thanks for meeting with us. We're building the conversational agent for Emporyum Tech and we need to understand the payment system in detail - methods, installments, interest rates, the whole thing.

**Andres:** Sure. I'll try to be precise because with payments, the details matter. One wrong number and users lose trust immediately. Let me grab my rate sheet... okay, ready.

**You:** Let's start with payment methods. What options do users have?

**Andres:** We support four payment methods currently. Each one has different characteristics:

1. **PSE (Pagos Seguros en Linea)** - This is a bank transfer system. Very popular in Colombia. The payment is essentially instant - well, technically it takes about 30 seconds to confirm on our side, but from the user's perspective it's immediate. No additional fees. Works with most Colombian banks. The user selects their bank, gets redirected to the bank's portal, authenticates, and approves the transfer. Then they come back to us.

2. **Tarjeta de Credito / Debito** - Credit and debit cards. We accept Visa, Mastercard, and American Express. Processing is instant. Standard stuff. We use tokenization for stored cards so returning users can pay with one click. The bot should know that we accept both credit and debit, because users ask this a lot: "aceptan tarjeta debito?" (do you accept debit?). Yes, we do.

3. **Efecty** - This is cash payment through Efecty points, which are physical locations all over Colombia. Think of it like paying your utilities bill at a store. The user gets a payment reference code after placing the order, takes it to any Efecty point, and pays in cash. Processing time is 1 to 2 business days after the cash is received. Important: the order is in "pending payment" status until the cash payment is confirmed. If the user doesn't pay within 48 hours, the order is automatically cancelled.

4. **Bancolombia A la Mano** - This is Bancolombia's mobile wallet. Very popular among users who don't have traditional bank accounts. The payment is confirmed same day, usually within a few hours. The user gets a reference code and pays through the Bancolombia A la Mano app.

**Andres:** One thing the bot should be clear about: you pick your payment method at checkout. You can't change it after the purchase is confirmed. Users ask this ALL the time: "puedo cambiar el metodo de pago?" (can I change the payment method?). The answer is no. If they really need to change it, they'd have to cancel the order and place a new one, but that's... well, technically it's possible but it's a hassle and we don't recommend it.

**You:** Got it. Now the big one - installments and interest. Walk me through that.

**Andres:** Alright, pay attention because this is where it gets detailed.

Our installment plans are available on purchases of **$50,000 COP or more**. Below that threshold, it's pay-in-full only. Here are the plans:

| Plan | Duration | Monthly Interest Rate | Notes |
|------|----------|----------------------|-------|
| 1 cuota | 1 month | 0% | Full payment, no interest |
| 3 cuotas | 3 months | 1.2% monthly | |
| 6 cuotas | 6 months | 1.5% monthly | Most popular |
| 12 cuotas | 12 months | 1.8% monthly | |
| 24 cuotas | 24 months | 2.0% monthly | Only for purchases > $500,000 COP |

**Andres:** Now, the 24-month plan has an additional requirement: the purchase must be over $500,000 COP. We don't offer 24 months for smaller amounts because the monthly payments would be ridiculously small and the administrative cost doesn't justify it.

**You:** How does the interest calculation work? Users are going to ask for specifics.

**Andres:** Right, so... well, technically, we could do a declining balance calculation where the interest is applied to the remaining principal each month, and the payment varies slightly. But for the bot - and honestly for our user-facing communications - we use a **simplified flat rate model**. It's easier for users to understand and easier for the bot to calculate.

Let me give you a concrete example. Say a user buys something for **$500,000 COP** and chooses **6 cuotas (months)**:

- Monthly interest rate: 1.5%
- Monthly interest amount: $500,000 x 1.5% = $7,500
- Monthly principal payment: $500,000 / 6 = $83,333
- **Total monthly payment: $83,333 + $7,500 = $90,833** (approximately $90,833 per month)
- **Total cost: $90,833 x 6 = $545,000**
- **Total interest paid: $45,000**

So the formula is simple:
- `cuota_mensual = (monto / numero_cuotas) + (monto * tasa_mensual)`
- `total_a_pagar = cuota_mensual * numero_cuotas`

**Andres:** I know the real financial math is more complex with amortization schedules and all that, but this is what the bot should use. Users want a quick answer: "cuanto me queda la cuota?" (how much is my monthly payment?). Give them this calculation.

**You:** Let me make sure I understand. Can you walk through another example, maybe with the 12-month plan?

**Andres:** Sure. Let's say a user buys a laptop for **$1,200,000 COP** and picks **12 cuotas**:

- Monthly interest rate: 1.8%
- Monthly interest amount: $1,200,000 x 1.8% = $21,600
- Monthly principal: $1,200,000 / 12 = $100,000
- **Total monthly payment: $100,000 + $21,600 = $121,600**
- **Total cost: $121,600 x 12 = $1,459,200**
- **Total interest paid: $259,200**

So the user pays $259,200 in interest over 12 months. That's about a 21.6% total cost of credit. It's not cheap, but it's competitive for the Colombian market. For context, credit cards here charge anywhere from 1.8% to 3% monthly depending on the bank, so our rates are on the lower end.

The bot should be able to do this math for any purchase amount and any plan. If a user asks "si compro algo de 800 mil en 6 cuotas, cuanto pago al mes?" (if I buy something for 800k in 6 installments, how much do I pay monthly?), the bot should calculate it on the spot:

- $800,000 / 6 = $133,333 principal
- $800,000 x 1.5% = $12,000 interest
- Monthly: $145,333

**Andres:** Oh, and one important nuance: the 1-cuota plan (single payment) is really just paying in full at checkout. There's no "one month to pay" - it's immediate. I just listed it as "1 cuota" because that's how it appears in the payment selection screen. The 0% interest is because... well, there are no installments. It's just a regular purchase.

**You:** Got it. What about the relationship between payment methods and installments? Can all payment methods use installments?

**Andres:** Good question. No. Installment plans are only available with **credit card** payments. Not debit cards, not PSE, not Efecty, not A la Mano.

Well, technically... wait, let me be precise. We're working on extending installments to PSE through a partnership with some banks, but that's not live yet. As of today: installments = credit card only. All other methods are pay-in-full.

The bot needs to handle this clearly. If someone says "quiero pagar en 6 cuotas por PSE" (I want to pay in 6 installments via PSE), the bot should say: "Los planes de cuotas actualmente estan disponibles solo con tarjeta de credito. Con PSE el pago se realiza de contado. Quieres que te explique los planes de cuotas con tarjeta?" (Installment plans are currently available only with credit card. With PSE the payment is in full. Would you like me to explain the credit card installment plans?)

**You:** What about late payments? What happens if someone misses a due date?

**Andres:** Late payments. Okay. So when a user is late on a payment, the interest rate increases to **1.5 times the regular rate**. So if they're on the 6-month plan at 1.5% monthly, their late rate becomes 2.25% monthly on the overdue amount.

We track the number of days late. The system categorizes them:

- **1-15 days late**: We send reminders (push notification + email). The increased rate applies but we're still relatively gentle about it.
- **16-30 days late**: More aggressive reminders. The user's account gets flagged.
- **31-60 days late**: Account restricted - they can't make new purchases until they catch up.
- **61+ days late**: Goes to our collections process. At this point, the bot should redirect the user to our specialized collections team. But, well, technically the collections bot is a separate system - I think another team is building that.

The bot should be able to tell users how many days late they are if they ask, and what the penalty interest looks like. But for anything related to negotiation of late payments - restructuring, settlements, that kind of thing - the bot should escalate to a human agent. The bot is NOT authorized to make deals on late payments.

**You:** Understood. What about early payoff? Can users pay ahead of schedule?

**Andres:** Yes! And this is actually something we want to encourage. Early payoff has **no penalty**. Zero. If a user has a 12-month plan and wants to pay it all off in month 3, they can do that and they save on the remaining interest.

The bot should explain it like: "Si pagas anticipadamente, no hay penalidad y te ahorras los intereses de las cuotas restantes." (If you pay early, there's no penalty and you save on interest from the remaining installments.)

The user can do an early payoff through the app under "Mis Pagos" > "Pago Anticipado" or by contacting support.

**You:** What about refinancing? Can users change their installment plan after purchase?

**Andres:** No. Refinancing is **NOT available**. Once you pick your plan at checkout, that's it. This is a hard policy.

If a user asks about refinancing - "puedo cambiar mis cuotas de 6 a 12?" (can I change from 6 to 12 installments?) - the bot should say clearly that it's not possible through the bot or the app, and redirect them to human support. I'll be honest, even human support rarely does this, but at least there they can evaluate special cases.

The bot should NOT say "it's impossible" because, well, technically, in very special circumstances, support might make an exception. But it should say something like: "El cambio de plan de cuotas no esta disponible a traves de este canal. Te recomiendo contactar a nuestro equipo de soporte para que puedan evaluar tu caso." (Changing the installment plan is not available through this channel. I recommend contacting our support team so they can evaluate your case.)

**You:** What about payment receipts? Users asking for proof of payment?

**Andres:** Payment receipts are available in the app. The path is: "Mis Pagos" > select the payment > "Ver Comprobante" (View Receipt). The bot should direct users there. We also send a receipt by email after every payment, so they can check their email too.

If the user says they didn't receive the email receipt, the bot should suggest checking spam/junk folder first. If it's still not there, they can download it from the app. If the app doesn't show it either, then escalate to support because that might be a technical issue.

**You:** Any other payment-related edge cases we should know about?

**Andres:** Let me think...

Oh yes. **Failed payments**. Sometimes a card payment fails. Common reasons: insufficient funds, expired card, bank declined it, or 3DS authentication failed (that's the SMS code verification some banks require). The bot should suggest:

1. Try again - sometimes it's a temporary bank issue
2. Check that the card details are correct
3. Try a different payment method
4. If it keeps failing, contact their bank

And one more thing: **payment schedule visibility**. Users often ask "cuando es mi proximo pago?" (when is my next payment?). The bot should tell them that their full payment schedule is visible in the app under "Mis Pagos" > "Calendario de Pagos". Each installment has a due date, and they get a push notification 3 days before it's due.

**Andres:** Actually, you know what, let me add one more thing. Users sometimes ask "puedo pagar mas de una cuota a la vez?" (can I pay more than one installment at once?). The answer is yes. They can pay multiple installments at once through the app. It's basically a partial early payoff. Same benefit - they save on interest for those installments.

And regarding the minimum purchase for installments - if someone tries to buy something for $30,000 on installments, the bot should tell them: "Los planes de cuotas estan disponibles para compras desde $50,000 COP. Para compras menores, el pago es de contado." (Installment plans are available for purchases from $50,000 COP. For smaller purchases, payment is in full.)

**You:** Perfect. This is really thorough. What about users who ask about credit limits? Do we have a concept of how much a user can purchase on installments?

**Andres:** Yes, but it's tricky. Every user has an **Emporyum Tech credit limit** that's determined during their registration. It's based on their credit score, income, and other risk factors. But - and this is important - the bot should NOT tell users what their credit limit is. That information is available in the app under "Mi Perfil" > "Mi Cupo" (My Credit Limit), but the bot should redirect them there rather than stating the number.

Why? Because credit limits are sensitive financial information and we don't want them floating around in chat logs. The bot should say: "Puedes consultar tu cupo disponible en la app, en Mi Perfil > Mi Cupo. Ahi veras tu cupo total y cuanto tienes disponible." (You can check your available credit in the app, under My Profile > My Credit Limit. There you'll see your total limit and how much you have available.)

If a user tries to make a purchase that exceeds their available credit, the checkout will fail. The bot should suggest paying with a different method or making a partial payment. But again, don't display the actual limit number in the chat.

**You:** What about auto-pay? Can users set up automatic payments?

**Andres:** Yes! Auto-pay is available through the app. The user goes to "Mis Pagos" > "Pago Automatico" and registers a credit or debit card. On each due date, we automatically charge the installment amount. They get a confirmation notification after each auto-charge.

The bot should encourage this because it prevents late payments. Something like: "Para evitar retrasos en tus pagos, puedes activar el pago automatico en la app. Asi tu cuota se descuenta automaticamente de tu tarjeta en la fecha de vencimiento." (To avoid late payments, you can activate auto-pay in the app. Your installment will be automatically charged to your card on the due date.)

Users can cancel auto-pay at any time. It doesn't affect their installment plan - they just go back to manual payments.

**You:** And what happens if the auto-pay charge fails? Like, insufficient funds?

**Andres:** Good edge case. If the auto-pay fails, we retry once more the next business day. If it fails again, the user gets a notification saying auto-pay failed and they need to make a manual payment. The late payment penalties start from the original due date, not from the retry date. So if the due date is the 15th and auto-pay fails on the 15th and retry fails on the 16th, the user is late from the 15th.

The bot should know this: "Si tu pago automatico falla, intentaremos un segundo cobro al dia habil siguiente. Si tambien falla, deberas realizar el pago manualmente para evitar intereses de mora." (If your auto-pay fails, we'll attempt a second charge the next business day. If it also fails, you'll need to make a manual payment to avoid late fees.)

**You:** Makes sense. Anything else?

**Andres:** I think that covers it. Oh, one more thing - the bot should never show or handle actual payment credentials. No card numbers, no bank passwords, nothing like that. If a user tries to type their card number in the chat, the bot should immediately tell them not to share sensitive financial information through the chat and redirect them to the secure payment page in the app. Security is paramount.

And interest rates can change. The ones I gave you are current as of today, but they might be adjusted. The KB should have them clearly documented so when they change, it's easy to update.

**You:** One last thing - how should the bot respond when someone asks general questions like "como funcionan los pagos?" or "explícame las cuotas"? Like, a general overview.

**Andres:** The bot should give a concise summary. Something like:

"En Emporyum Tech puedes pagar de contado o en cuotas:

**Pago de contado:** Puedes usar PSE (transferencia bancaria), tarjeta credito/debito, Efecty (efectivo), o Bancolombia A la Mano.

**Pago en cuotas (solo tarjeta de credito, compras desde $50,000 COP):**
- 1 cuota: 0% interes
- 3 cuotas: 1.2% mensual
- 6 cuotas: 1.5% mensual
- 12 cuotas: 1.8% mensual
- 24 cuotas: 2.0% mensual (compras desde $500,000)

Quieres que te calcule las cuotas para un producto especifico?"

Keep it clean, give them the key facts, and offer to go deeper. That's the ideal interaction pattern for payment questions.

**You:** Understood. Thanks, Andres. Very clear.

**Andres:** No problem. If the bot gets the numbers wrong, I'll hear about it from Risk Compliance, so... double check the rates. And feel free to ping me if something's unclear.

---

## Key Information Summary

_(For interviewer reference - candidates should extract this themselves)_

### Topics to Extract
- **METODOS DE PAGO**: 4 methods (PSE, Card, Efecty, Bancolombia A la Mano) with processing times and characteristics. Can't change payment method after purchase.
- **CUOTAS E INTERESES**: 5 installment plans with specific rates. Flat rate calculation model. Minimum $50,000 COP. 24 months requires >$500,000. Late payments at 1.5x rate. Early payoff with no penalty. No refinancing (escalate to support).

### Response Language
All bot responses should be in **Spanish** since the bot serves Colombian users.

### Edge Cases
- Failed payments: suggest retry, different method, contact bank
- Late payments: rate increases, account restrictions at 31+ days, collections at 61+
- Refinancing: not available, redirect to human support
- Payment receipts: available in app "Mis Pagos"
- Never handle payment credentials in chat
- Below $50,000 COP: no installment plans available
