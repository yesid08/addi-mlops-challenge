# Stakeholder Interview: Operations Team

**Date:** Tuesday, 9:30 AM
**Interviewee:** Laura Herrera, Operations Lead - Logistics & Customer Experience
**Location:** Meeting Room "Monserrate", Emporyum Tech HQ Bogota
**Attendees:** Laura (Operations), You (AI Team)

---

## Transcript

**You:** Laura, thanks for meeting with us. We're building the Emporyum Tech bot and need to understand the full purchase flow, order tracking, and especially the returns process.

**Laura:** Hi! Yes, super happy to help. I've been dealing with customer support tickets for two years now, so I have a LOT of opinions about what the bot should handle. I actually have a whole process document I'm going to walk you through. Let's do this systematically.

**You:** Perfect. Let's start with the purchase flow. How does someone actually buy something on Emporyum Tech?

**Laura:** Okay, so the purchase flow has well-defined steps. This is really important because users often get confused about where they are in the process. The bot should be able to guide them through each step:

**Step 1: Account verification**
Before anything else, the user needs to have a verified Emporyum Tech account. This means they've completed the sign-up, verified their email, and confirmed their phone number. If they haven't done this, they can't purchase. The bot should check this first.

**Step 2: Browse the catalog**
They can browse by category, search by keyword, or get recommendations. Maria on the product team can tell you more about this part.

**Step 3: Add to cart**
When they find what they want, they add it to the cart. They can add multiple items. The cart shows the subtotal, any applicable discounts, and estimated shipping cost. Items in the cart are NOT reserved - if someone else buys the last unit while it's in your cart, you'll get a stock notification when you try to checkout.

**Step 4: Select payment method**
At checkout, they choose from PSE, card, Efecty, or Bancolombia A la Mano. Andres can give you the details on each one.

**Step 5: Choose installment plan**
If the purchase is over $50,000 COP and they're paying by card, they select their installment plan. If paying by PSE, Efecty, or A la Mano, it's always a single payment.

Wait, actually, I need to correct that. Installment plans are available through card payments and also through PSE for certain banks. Let me check... you know what, Andres would know the exact rules. The important thing for the bot is: if the user is eligible for installments, the option appears at checkout.

**Step 6: Confirm purchase**
They review everything - items, total, payment method, shipping address - and confirm. This is the point of no return, basically.

**Step 7: Confirmation email**
Immediately after confirming, they get an email with the order details, order number, and estimated delivery date. The bot should tell users to check their email (and spam folder) for this confirmation.

**Step 8: Track delivery**
They can track their order in the app under "Mis Pedidos" or by giving the order number to the bot.

**You:** That's very clear. Now let's talk about order statuses. What are the possible states?

**Laura:** Right, so an order goes through these statuses, in order:

1. **CONFIRMADO** (CONFIRMED) - Payment has been received and the order is in our system. For Efecty payments, this status appears only after the cash payment is confirmed (remember, 1-2 business days).

2. **EN PREPARACION** (PREPARING) - The warehouse team has received the order and is picking and packing the items. This usually takes 1 business day but can take up to 2 during peak seasons like Black Friday or Christmas.

3. **ENVIADO** (SHIPPED) - The package has been handed off to the delivery carrier. At this point, the user gets a tracking number. We use several carriers depending on the destination: Servientrega, Coordinadora, InterRapidisimo, and Envia for some regional routes.

4. **EN TRANSITO** (IN TRANSIT) - The package is on its way to the delivery address. This is the status that lasts the longest. The user can track it with the tracking number.

5. **ENTREGADO** (DELIVERED) - The package has been delivered and confirmed. The carrier gets a signature or photo confirmation. The 15-day return window starts counting from this date - this is really important.

6. **CANCELADO** (CANCELLED) - The order was cancelled. This can happen in two ways:
   - User cancellation: the user can cancel any time before the status reaches ENVIADO (SHIPPED). Once it's shipped, they can't cancel - they'd have to wait and do a return.
   - System cancellation: if payment isn't received within 48 hours (for Efecty/A la Mano), the system auto-cancels.

**Laura:** Oh, I should mention - there's also an implicit status of **PAGO PENDIENTE** (PENDING PAYMENT) for Efecty and A la Mano orders, but it's kind of a pre-status before CONFIRMADO. The user has placed the order but hasn't actually paid yet. The bot should be clear about this: "Tu pedido ha sido registrado pero aun no hemos recibido tu pago. Tienes 48 horas para realizar el pago en [Efecty/Bancolombia A la Mano]."

**You:** Got it. Now, delivery times - how long does it take?

**Laura:** Delivery times depend on the destination city. These are in **business days**, starting from the CONFIRMADO status:

| Destination | Delivery Time |
|-------------|---------------|
| Bogota | 3 business days |
| Medellin | 5 business days |
| Cali | 5 business days |
| Barranquilla | 5 business days |
| Other major cities (Cartagena, Bucaramanga, Pereira, etc.) | 7 business days |
| Rural areas / small towns | Up to 10 business days |

**Laura:** The bot should always say "dias habiles" (business days), not just "dias." Users get confused and think it means calendar days, then they call on Saturday complaining their package hasn't arrived. Weekends and holidays don't count.

Also, during peak seasons (Black Friday, Amor y Amistad, Christmas), delivery times can increase by 2-3 business days. The bot should mention this during those periods if applicable. But outside of peak season, these times are pretty reliable. We hit our delivery SLA about 92% of the time.

**You:** Perfect. Now the big one - returns and refunds. Walk me through this carefully.

**Laura:** Okay. THIS IS REALLY IMPORTANT. Returns are the most complex flow the bot will handle, and it's where we get the most support tickets. I'm going to be very detailed here.

### Returns Policy

First, the policy fundamentals:

- **Return window**: 15 calendar days from the delivery date (the ENTREGADO status date). After 15 days, no returns accepted, no exceptions. The bot should be firm about this.
- **Product condition**: The product must be unused, in its original packaging, with all original accessories, tags, and documentation. If the user took off the tags or opened a sealed product, it might not qualify.
- **Non-returnable items**: Some products CANNOT be returned under any circumstances:
  - Ropa interior (underwear) - hygiene reasons
  - Audifonos / earphones / earbuds - hygiene reasons
  - Productos personalizados o grabados (personalized or engraved items) - they were made custom
  - Productos perecederos (perishable goods) - though we barely sell any of these
  - Software licenses or digital products - once activated, no return

### The Multi-Step Returns Flow

This is really important for the bot because it's NOT a one-shot interaction. It requires multiple exchanges with the user. Let me walk you through the exact flow:

**--- STEP 1: Return Request ---**

The user says something like "quiero devolver un producto" (I want to return a product) or "quiero hacer una devolucion" (I want to make a return).

The bot needs to verify three things before proceeding:

**(a) Does the order exist?**
The bot should ask for the order number or look it up from the user's account. If the order doesn't exist or doesn't belong to this user, stop here. "No encontramos un pedido con ese numero asociado a tu cuenta." (We couldn't find an order with that number associated to your account.)

**(b) Is it within the 15-day return window?**
Calculate the number of days since the ENTREGADO (delivered) date. If it's more than 15 calendar days, the return is not eligible. "Lamentablemente, el plazo de 15 dias para devolucion ya ha vencido. Tu pedido fue entregado el [date]." (Unfortunately, the 15-day return window has expired. Your order was delivered on [date].)

If the order hasn't been delivered yet (status is not ENTREGADO), tell the user they need to wait for delivery before initiating a return. Or, if the order is in CONFIRMADO or EN PREPARACION, suggest cancellation instead since that's simpler.

**(c) Is the product returnable?**
Check if any items in the order are in the non-returnable list. If the specific product they want to return is non-returnable, inform them: "Este producto no es elegible para devolucion por politicas de higiene / por ser un producto personalizado." (This product is not eligible for return due to hygiene policies / because it's a personalized product.)

If all three checks pass, the bot should ask the user **why** they want to return the product. This is required.

"Entendido, tu pedido es elegible para devolucion. Por favor, indicanos el motivo de la devolucion:
1. El producto llego danado
2. Recibi un producto diferente al que pedi
3. El producto no cumple mis expectativas
4. Ya no lo necesito
5. Otro motivo"

(Understood, your order is eligible for return. Please tell us the reason for the return.)

**--- STEP 2: Confirm Return & Schedule Pickup ---**

Once the user provides a reason, the bot proceeds to:

1. **Confirm the return**: "Hemos registrado tu solicitud de devolucion para el pedido #[order_number]. Motivo: [reason]."

2. **Schedule pickup**: "Programaremos la recoleccion del producto en tu direccion registrada en los proximos 3-5 dias habiles. Recibirás un correo con los detalles de la recoleccion." (We'll schedule a pickup at your registered address within the next 3-5 business days. You'll receive an email with the pickup details.)

3. **Explain refund timeline**: "Una vez recibamos el producto y verifiquemos su estado, procesaremos tu reembolso en un plazo de 5 a 10 dias habiles. El reembolso se realizara al mismo metodo de pago que utilizaste para la compra." (Once we receive the product and verify its condition, we'll process your refund within 5 to 10 business days. The refund will be made to the same payment method you used for the purchase.)

4. **Important packaging instructions**: "Por favor, empaca el producto en su empaque original, incluyendo todos los accesorios y documentacion. Si no tienes el empaque original, utiliza una caja resistente y protege bien el producto." (Please pack the product in its original packaging, including all accessories and documentation. If you don't have the original packaging, use a sturdy box and protect the product well.)

**Laura:** So you see, it's a two-step conversation minimum. Step 1 is verification and reason collection. Step 2 is confirmation and scheduling. The bot needs to maintain context between these steps - it can't forget the order number or the reason when moving to step 2.

**You:** What about special cases in the returns flow?

**Laura:** Good question. There are a few scenarios that require **immediate escalation to a human agent** instead of the normal flow:

1. **Order not received after expected delivery date**: If the tracking shows ENVIADO or EN TRANSITO but the delivery date has passed, this needs human investigation. The bot should say: "Vemos que tu pedido aun no ha sido entregado y ya paso la fecha estimada. Vamos a escalar esto a nuestro equipo de soporte para que investiguen con el transportador." (We see your order hasn't been delivered and the estimated date has passed. We'll escalate this to our support team to investigate with the carrier.) Then create a support ticket.

2. **Wrong item received**: If the user received a different product than what they ordered, this is an operational error on our side. Don't go through the normal return flow - escalate immediately. "Lamentamos que hayas recibido un producto diferente. Este caso requiere atencion inmediata de nuestro equipo de soporte. Vamos a escalarlo ahora." (We're sorry you received a different product. This case requires immediate attention from our support team. We'll escalate it now.)

3. **Damaged product**: If the product arrived damaged, the bot should ask the user to provide photos of the damage (through the app's support chat which supports image uploads). Then escalate to a human agent who can evaluate the damage and expedite the return/replacement. "Para procesar tu reclamo por producto danado, necesitamos que nos envies fotos del producto y del empaque. Nuestro equipo de soporte evaluara tu caso de forma prioritaria." (To process your damaged product claim, we need you to send us photos of the product and packaging. Our support team will evaluate your case as a priority.)

**Laura:** For all three escalation cases, the bot should give the user a reference number and an estimated response time. Escalated cases should be resolved within 24-48 hours.

**You:** What about exchanges? Can users swap a product for a different one?

**Laura:** Hmm, not directly. We don't have a "swap" or exchange flow. If a user wants a different product, they need to:

1. Return the original product (following the returns flow above)
2. Place a new order for the product they actually want

The bot should explain this clearly: "No manejamos cambios directos, pero puedes solicitar la devolucion del producto actual y realizar una nueva compra del producto que deseas." (We don't handle direct exchanges, but you can request a return of the current product and place a new order for the product you want.)

I know it's not ideal, but that's how our system works right now. We've talked about implementing a proper exchange flow, but it's not on the roadmap yet.

**You:** And refund timelines? Let me make sure I have this right.

**Laura:** Yes, let me be very specific:

- **Refund timeline**: 5 to 10 business days after we receive and inspect the returned product.
- **Refund method**: Always to the same payment method used for the original purchase.
  - Card payments: refund appears on the card statement in 5-10 business days
  - PSE: refund to the same bank account in 5-7 business days
  - Efecty: this is tricky - we issue a bank transfer to the user's registered bank account since we can't send cash back through Efecty. This can take up to 10 business days.
  - Bancolombia A la Mano: refund to the same A la Mano account in 3-5 business days (actually the fastest)

**Laura:** One more thing on returns: if the user had a promotion or discount applied to the order, the refund is for the amount actually paid, not the original price. So if they got a 15% Tech Week discount, the refund is for the discounted amount. The bot should be prepared to explain this because users sometimes think they'll get the full catalog price back.

**You:** This is incredibly helpful. Anything else on the operations side?

**Laura:** Let me think... Oh! Order cancellation - I should elaborate on that. A user can cancel an order as long as it hasn't reached ENVIADO status. The bot should guide them:

"Puedes cancelar tu pedido siempre que aun no haya sido enviado. ¿Deseas cancelar el pedido #[order_number]?" (You can cancel your order as long as it hasn't been shipped yet. Do you want to cancel order #[order_number]?)

If they confirm, the cancellation is immediate and the refund follows the same timelines I mentioned above.

If the order is already ENVIADO or beyond, the bot should say: "Tu pedido ya fue enviado, por lo que no es posible cancelarlo. Una vez lo recibas, puedes solicitar una devolucion si lo deseas." (Your order has already been shipped, so it cannot be cancelled. Once you receive it, you can request a return if you wish.)

Oh, and one more thing about delivery: users can track their order in real time through the app. The bot should tell them: "Puedes ver el estado actualizado de tu pedido en la app, en la seccion 'Mis Pedidos'. Tambien puedes usar el numero de seguimiento que te enviamos por correo." (You can see the updated status of your order in the app, under 'My Orders'. You can also use the tracking number we sent you by email.)

That's it from my side. I think I've covered everything. If the bot can handle the returns flow correctly - the two steps, the validations, the escalation cases - that alone would reduce our support tickets by like 40%. That's the dream.

**You:** That would be great. Thanks, Laura!

**Laura:** Thank you! Oh wait, one last thing - the bot should always verify the user's identity before showing any order information. We can't just let anyone look up random order numbers. The user needs to be authenticated in the app, or the bot should confirm their identity by asking for the email associated with the account. Security first!

---

## Key Information Summary

_(For interviewer reference - candidates should extract this themselves)_

### Topics to Extract
- **COMO COMPRAR**: 8-step purchase flow from account verification to delivery tracking.
- **ESTADO DE PEDIDO**: 6 order statuses (CONFIRMADO, EN PREPARACION, ENVIADO, EN TRANSITO, ENTREGADO, CANCELADO) plus implicit PAGO PENDIENTE. Delivery times by city.
- **DEVOLUCIONES Y CAMBIOS**: Multi-step flow. Step 1: verify order, check window, check eligibility, ask reason. Step 2: confirm return, schedule pickup, explain refund timeline. Escalation cases. Non-returnable items list.

### Response Language
All bot responses should be in **Spanish** since the bot serves Colombian users.

### Multi-Step Flow Details
The returns/refund flow is the key multi-step interaction. Candidates must implement state tracking across:
- Step 1: Validation + reason collection
- Step 2: Confirmation + logistics
- Escalation paths for special cases (not received, wrong item, damaged)

### Edge Cases
- Cancellation only before ENVIADO status
- No direct exchanges - return + new order
- Refund to same payment method, discounted amount
- Non-returnable categories (hygiene, personalized, perishable)
- Identity verification before showing order info
- Business days vs calendar days distinction
