# Stakeholder Interview: Product Team

**Date:** Monday, 10:00 AM
**Interviewee:** Maria Gonzalez, Product Manager - Catalog & Discovery
**Location:** Meeting Room "Cafe Tinto", Emporyum Tech HQ Bogota
**Attendees:** Maria (Product), You (AI Team)

---

## Transcript

**You:** Maria, thanks for taking the time. We're building the conversational bot for Emporyum Tech and we need to understand how the catalog and recommendations work so we can train the agent properly.

**Maria:** Of course! I'm so excited about this project. We've been wanting a bot that really *gets* our catalog for ages. Let me pull up my notes... okay, so where should we start?

**You:** Let's start with the catalog structure. How is it organized?

**Maria:** Right. So our catalog is organized into four main categories. Let me walk you through them:

1. **Electrónica** - this is our biggest revenue driver, honestly. It includes:
   - Smartphones and tablets
   - Laptops and computers
   - Audio (headphones, speakers, earbuds)
   - Gaming (consoles, accessories)
   - Accessories (chargers, cases, cables)
   - Smart Home devices (we just added this one last quarter)

2. **Hogar** - Home & Living, which has been growing a lot:
   - Furniture (living room, bedroom, office)
   - Kitchen appliances (blenders, air fryers - air fryers are HUGE right now)
   - Decoration
   - Bedding & Bath
   - Garden & Outdoor

3. **Moda** - Fashion:
   - Women's clothing
   - Men's clothing
   - Shoes (both genders)
   - Bags & Accessories
   - Sportswear

4. **Belleza** - Beauty & Personal Care:
   - Skincare
   - Makeup
   - Hair care
   - Fragrances
   - Personal care devices (like those LED face masks that are trending)

**You:** Got it. And how does each product look in the system?

**Maria:** Each product has a standard set of attributes. The ones the bot should care about are:

- **Product name** - the display name
- **Price** - in COP (Colombian Pesos), always
- **Category and subcategory** - where it lives in the tree
- **Rating** - 1 to 5 stars, based on verified buyer reviews
- **Stock status** - this is important: it's either "disponible", "pocas unidades" (less than 5 left), or "agotado" (out of stock)
- **Description** - a short text about the product

Oh, and there's also a product ID but I don't think the bot needs to expose that to users. Actually, it might be useful for looking things up... you can decide on that.

**You:** That helps. Now tell me about recommendations. How should the bot suggest products?

**Maria:** Okay this is my favorite part. So the recommendation logic should consider several signals:

**When we have user history:**

The bot should look at what they've bought before and what categories they tend to browse. So if someone has purchased three electronics items, and they ask "recomiendame algo" (recommend me something), we should lean towards electronics. But not *exclusively* - we want to also surface items from other categories they might like.

If the user mentions a budget, that's gold. We should absolutely filter by that. Like if someone says "busco algo por menos de doscientos mil" ($200,000 COP), we narrow it down to that range. We don't want to show them a $3,000,000 laptop if they said they have $200,000.

Trending products should also be factored in. We track what's selling well in the last 7 days, and those get a boost in recommendations.

Oh, and category preference! If a user asks about a specific category like "quiero algo para mi cocina" (I want something for my kitchen), we obviously narrow down to Hogar > Kitchen.

**When there's NO user history:**

This is super common because a lot of users are new. In that case, we fall back to trending products. Just show them what's popular. We can organize it by category: "These are trending in Electronics, these in Fashion..." etc. Give them a taste of everything.

**Maria:** Oh wait, another thing I forgot to mention - seasonal relevance matters too. Like, right now in December we push more gift-oriented products. But honestly, for the bot's first version, trending + purchase history + budget is enough. We can add seasonality later. Don't overcomplicate it.

**You:** And how should the bot actually present these recommendations? Like, what does a good recommendation message look like?

**Maria:** Great question! So the bot should present each product with its key info: name, price, and one short reason why it's being recommended. Let me give you an example of what a good response would look like:

"Basandome en tus compras anteriores, te recomiendo:

1. **Samsung Galaxy Buds Pro** - $450.000 COP - Muy popular esta semana, 4.7 estrellas
2. **JBL Flip 6** - $380.000 COP - Complementa tus audifonos, excelente calidad de sonido
3. **Apple AirPods 3** - $520.000 COP - Compatible con tu iPhone, en promocion Tech Week (-15%)

Quieres que te muestre mas detalles de alguno?"

See? Each one has a reason. "Popular this week," "complements your other purchases," "on promotion." That's what makes users trust the recommendation. If the bot just lists product names and prices, it feels like a catalog dump. We want it to feel like a knowledgeable friend who knows the store.

**You:** That makes sense. What about when the user provides contradictory signals? Like they say they want electronics but then ask about a dress?

**Maria:** Ha! That happens more than you'd think. The bot should just roll with it. If a user who's been browsing electronics suddenly asks about fashion, just switch context. Don't be rigid about it. The purchase history is a *signal*, not a prison. Maybe they're shopping for themselves and for a gift. People don't shop in neat little boxes.

But - and this is important - the bot should still remember the conversation context. So if they were looking at phones and then ask about dresses and then say "actually, let's go back to that phone" - the bot should know what phone they were talking about. Conversation memory matters a lot for a shopping experience.

**You:** And what about brands? Do you have any brand-specific guidelines?

**Maria:** We carry multiple brands in each category. We don't have exclusive partnerships with any brand, so the bot should be neutral. It should NEVER say "Samsung is better than Apple" or anything like that. If a user asks for a brand comparison, the bot can list features of each product but should not make subjective quality judgments. Let the ratings speak for themselves.

We do have "marca destacada" (featured brand) partnerships sometimes - like, right now we have a Samsung feature where their products get extra visibility. But the bot shouldn't preferentially push one brand over another unless there's a promotion active for that brand. And even then, it should present it as "Samsung products are currently on promotion" not as "Samsung is the best."

**You:** What if a user asks about product availability in a specific city? Does stock vary by location?

**Maria:** No, and this is actually a common misconception. Our catalog is national - same stock for everyone. We ship from central warehouses in Bogota and Medellin. The delivery TIME varies by city (Laura can tell you about that), but the product availability is the same regardless of where the user is.

So if someone asks "esto esta disponible en Cali?" (is this available in Cali?), the answer is: if it's available in the catalog, it ships nationwide. The only thing that changes is how long delivery takes.

**Maria:** Oh, and one more thing about the catalog I should mention - we update it frequently. New products come in every week, prices can change during promotions, and stock status changes in real-time. The bot should never cache product information for too long. But that's more of a technical concern for your team. For the KB, just make sure the bot knows how to talk about the catalog structure and how recommendations work.

**You:** Makes sense. Let's talk about promotions and discounts. What's currently active?

**Maria:** Oh yes! So we always have promotions running. Here are the current active ones:

1. **"Tech Week"** - 15% off all Electronics category products. This one runs pretty frequently, almost every other month. It's one of our strongest promos.

2. **"Nuevo Usuario"** - 10% discount on the first purchase for new users. This is always active, it's part of our acquisition strategy. Every new customer gets this automatically.

3. **"Envio Gratis"** - Free shipping on orders over $200,000 COP. Also always active. This one is really important because shipping costs are one of the biggest friction points in e-commerce here in Colombia. I can't tell you how many abandoned carts we had before we introduced this.

4. **"Beauty Days"** - 20% off all Beauty category products. This runs quarterly, usually around the same time as fashion events.

5. **"Hogar Feliz"** - Up to 30% off selected Home products. The "up to" is important - not everything gets 30%. Some items are 10%, some 20%, and the flagship deals get 30%. The bot should say "hasta 30% de descuento" (up to 30% off).

**Maria:** Now here's something important for the bot: promotions can change. What's active today might not be active next month. But for the KB, we should document the current ones and the bot should present them accurately. If someone asks "hay alguna promocion?" (are there any promos?), the bot should list whatever promos are currently active.

And one more thing - promos don't stack. A user can't use "Nuevo Usuario" AND "Tech Week" on the same purchase. The system applies the better discount automatically, but the bot should be clear that promotions are not combinable. Users ask about this ALL the time.

**You:** Understood. What about edge cases? What should the bot NOT do?

**Maria:** Great question. This is where previous chat attempts have failed, so listen carefully:

**Out of stock products:**
When a product is "agotado" (out of stock), the bot should NOT just say "sorry, it's not available." That's a dead end. It should suggest similar alternatives. Like, "Este producto está agotado, pero te puedo recomendar estas opciones similares..." (This product is out of stock, but I can recommend these similar options...). We lose so many potential sales when bots just say "not available" and leave the user hanging.

**Products not in our catalog:**
If someone asks for something we clearly don't sell - like, I don't know, car insurance or groceries - the bot should redirect gracefully. Something like "Actualmente en Emporyum Tech nos especializamos en Electrónica, Hogar, Moda y Belleza. No manejamos ese producto, pero puedo ayudarte a encontrar algo en nuestras categorías." (Currently at Emporyum Tech we specialize in Electronics, Home, Fashion and Beauty. We don't carry that product, but I can help you find something in our categories.)

**NEVER compare prices with competitors:**
This is a hard rule from Legal. The bot must never, under any circumstances, say things like "our price is better than Mercado Libre" or "this is cheaper than at Falabella." If a user asks "is this cheaper than at X?", the bot should say something like "No puedo comparar precios con otros comercios, pero puedo mostrarte nuestras promociones activas para que obtengas el mejor precio." (I can't compare prices with other stores, but I can show you our active promotions so you get the best price.)

**NEVER make up products:**
The bot should never invent products that don't exist in our catalog. If someone asks for a "Samsung Galaxy S99 Ultra Mega Pro" that doesn't exist, don't just make up specs and a price. Say you don't have that specific product and offer to show what's available in that category.

**You:** What about gift purchases? People buying for someone else?

**Maria:** Oh, good point! Yes, this is really common especially around Mother's Day, Father's Day, Amor y Amistad (that's Colombia's Valentine's Day, in September), and Christmas. When a user says something like "busco un regalo para mi mama" (I'm looking for a gift for my mom), the bot should ask what she's into. Electronics? Beauty? Home? What budget? Does she have any specific needs?

The bot should NOT assume gender preferences. Don't automatically suggest Beauty products for women or Electronics for men. Ask first. We had complaints about this from an earlier version of our recommendation email campaigns. Let the user guide you.

Also, if it's clearly a gift scenario, the bot can mention that we offer gift wrapping for an additional $15,000 COP. It's not a huge thing but users appreciate knowing it exists. "Tambien ofrecemos empaque de regalo por $15.000 COP adicionales. Puedes seleccionarlo al momento del checkout." (We also offer gift wrapping for an additional $15,000 COP. You can select it at checkout.)

**Maria:** Actually, while we're on edge cases, there's one more I should mention - warranty questions. Users sometimes ask the bot about product warranties. We don't manage warranties directly - they're handled by the manufacturer. The bot should tell users: "La garantia de los productos es gestionada directamente por el fabricante. Puedes encontrar la informacion de garantia en la descripcion del producto o contactar al fabricante." (Product warranty is managed directly by the manufacturer. You can find warranty information in the product description or contact the manufacturer.) The bot should NOT make warranty promises on our behalf.

**Maria:** Oh! One more thing. When users ask for recommendations, the bot should try to give 3-5 options, not just one and not twenty. Three to five is the sweet spot. And it should briefly explain *why* it's recommending each one - like "este es popular" (this one is popular), "este tiene buenas reviews" (this one has great reviews), "este está en promocion" (this one is on sale). Users trust recommendations more when they understand the reasoning.

**You:** That's really helpful. Any other quirks the bot should know about?

**Maria:** Hmm... let me think. Oh yes - pricing is always in COP. Always. We don't do USD or anything else. And we display prices with the thousand separator dot, like $1.500.000. Make sure the bot formats prices correctly because users get confused when they see "1500000" without separators.

Also, if a user asks about a product and they're vague - like "quiero un celular bueno" (I want a good phone) - the bot should ask clarifying questions. What budget do they have? What do they use it for? Do they prefer a specific brand? Don't just dump the most expensive phone on them.

Ah, and one last thing... we have a wishlist feature in the app. The bot can suggest users add products to their wishlist if they're not ready to buy yet. Like "Si no estás listo para comprar, puedes agregarlo a tu lista de deseos y te notificamos cuando baje de precio." (If you're not ready to buy, you can add it to your wishlist and we'll notify you when the price drops.) That's a nice touch that reduces pressure on the user.

**You:** Perfect. I think we have everything we need from your side.

**Maria:** Amazing! I'm really excited to see how the bot handles recommendations. If you need me to clarify anything about specific product categories or test scenarios, just ping me on Slack. Oh, and if you want, I can send you a sample catalog export so you can see what the data looks like - but honestly for the bot's KB, you probably just need the category structure and the promotion details.

---

## Key Information Summary

_(For interviewer reference - candidates should extract this themselves)_

### Topics to Extract
- **RECOMENDACION DE PRODUCTOS**: How recommendations work based on history, budget, trending, category. Fallback to trending for new users. 3-5 suggestions with reasoning.
- **PROMOCIONES Y DESCUENTOS**: 5 active promos with specific discount percentages and conditions. Promos don't stack.

### Response Language
All bot responses should be in **Spanish** since the bot serves Colombian users.

### Edge Cases
- Out of stock: suggest alternatives, don't dead-end
- Not in catalog: redirect to available categories
- Never compare with competitors
- Never invent products
- Always use COP with proper formatting
- Ask clarifying questions for vague requests
