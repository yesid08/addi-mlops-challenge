# Stakeholder Interview: Platform Engineering Team

**Date:** Tuesday, 2:30 PM
**Interviewee:** Diego Moreno, Platform Engineering Manager
**Location:** Meeting Room "Guatape", Emporyum Tech HQ Bogota
**Attendees:** Diego (Platform Engineering), You (AI Team)

---

## Transcript

**You:** Diego, thanks for joining. We need to understand the app, account management, and common technical issues so the bot can help users with those things.

**Diego:** Hey, yeah. Happy to help. I've actually been looking forward to this because our support team gets buried in "how do I change my password" tickets. If the bot can handle even half of that, we're golden. Alright, let me pull up the app architecture... I mean, let me pull up the feature list. You don't need the architecture.

**You:** Let's start with what the app can do. Give me the full picture.

**Diego:** Sure. So Emporyum Tech is available on three platforms:

- **iOS app** - requires iOS 15 or later
- **Android app** - requires Android 10 or later
- **Web** - at emporyumtech.com, works on any modern browser (Chrome, Firefox, Safari, Edge)

All three have feature parity, meaning everything you can do on iOS you can do on Android and web. We use a... never mind the technical details. The point is, the experience is the same everywhere.

Here are the main features:

1. **Browse Catalog** - Browse by category, search by keyword, filter by price range, rating, brand. The search uses elast... I mean, it uses a smart search engine that handles typos and synonyms. So if someone types "audifono" without the accent, it still works.

2. **Product Search** - Users can search for specific products. The search bar supports natural language queries like "audifonos bluetooth baratos" (cheap bluetooth headphones). Results are sorted by relevance by default but can be sorted by price (low to high, high to low), rating, or newest.

3. **Order Tracking** - Under "Mis Pedidos" (My Orders). Shows all orders with their current status, tracking number, estimated delivery date. Users can tap on any order to see the full timeline of status changes.

4. **Payment Management** - Under "Mis Pagos" (My Payments). Shows upcoming payments, payment history, and the installment schedule. Users can make payments here, set up auto-pay, or do an early payoff.

5. **Saved Payment Methods** - Users can save credit/debit cards for quick checkout. Stored securely with... well, with proper encryption and tokenization. The bot doesn't need to explain the technical details, just that cards are stored securely.

6. **Installment Schedule** - Shows the full breakdown of each installment plan: due date, amount, status (paid, pending, overdue). Also shows total remaining balance and total interest.

7. **Push Notifications** - Users get notifications for:
   - Payment due in 3 days
   - Payment overdue
   - Order status changes (shipped, delivered)
   - Promotions and deals (if they opt in)
   - Security alerts (new login, password change)

8. **Wishlists** - Users can save products to their wishlist. They get notified if a wishlisted product goes on sale or comes back in stock.

9. **Delivery Address Management** - Users can save multiple delivery addresses and select the default one. They can add, edit, or delete addresses.

10. **Support Chat** - In-app support chat. This is where the bot will live, actually. The chat supports text and image uploads (for things like damaged product photos).

**You:** Great. Now let's talk about account management. What can users change themselves, and what requires support?

**Diego:** Good question. This is a really common source of confusion. Let me break it down clearly:

### Things the user CAN update themselves (through the app):

- **Phone number**: Under "Mi Perfil" > "Numero de Telefono". Requires SMS verification of the new number. The old number gets a notification that the phone was changed (security measure).

- **Email address**: Under "Mi Perfil" > "Correo Electronico". Requires verification of the new email. Important: this changes where they receive order confirmations, payment receipts, everything. The old email gets a notification too.

- **Delivery address**: Under "Mis Direcciones". They can add multiple addresses and set a default. No verification needed for this one.

- **Password**: Under "Mi Perfil" > "Seguridad" > "Cambiar Contrasena". They need to enter their current password plus the new one. Password requirements: minimum 8 characters, at least one uppercase, one lowercase, one number, and one special character. Yes, I know it's strict, but security team insists.

- **Notification preferences**: Under "Mi Perfil" > "Notificaciones". They can toggle each notification type on/off. But we strongly recommend keeping payment reminders on. The bot should mention this: "Te recomendamos mantener activadas las notificaciones de pago para no olvidar tus fechas de vencimiento." (We recommend keeping payment notifications enabled so you don't forget your due dates.)

### Things the user CANNOT update themselves:

- **Legal name (nombre legal)**: This is tied to their identity verification. If they need to change it (marriage, legal name change, typo during registration), they need to submit a support ticket with a copy of their official ID (cedula). Processing time: 3-5 business days.

- **ID number (numero de cedula)**: Same as above. This is their primary identifier in our system and it's linked to their credit assessment. Cannot be changed through the app. Requires a support ticket with documentation.

The bot should handle these gracefully: "Para actualizar tu nombre legal o numero de cedula, es necesario crear un ticket de soporte con una copia de tu documento de identidad. Nuestro equipo lo procesara en 3 a 5 dias habiles." (To update your legal name or ID number, you need to create a support ticket with a copy of your identity document. Our team will process it in 3 to 5 business days.)

**You:** What about password reset? Users who forgot their password?

**Diego:** Classic. So the password reset flow is:

1. On the login screen, tap "Olvide mi contrasena" (I forgot my password)
2. Enter the email associated with the account
3. We send a password reset link to that email (valid for 30 minutes)
4. User clicks the link, enters a new password
5. Done. All active sessions are terminated for security.

If the user doesn't have access to their email anymore... that's a problem. They'd need to contact support and verify their identity through other means (phone number, ID document). The bot should suggest the email reset flow first, and only escalate to support if they can't access their email.

The bot should say something like: "Para restablecer tu contrasena, ingresa a la pantalla de inicio de sesion y selecciona 'Olvide mi contrasena'. Te enviaremos un enlace a tu correo electronico registrado." (To reset your password, go to the login screen and select 'I forgot my password'. We'll send a link to your registered email.)

**You:** Two-factor authentication - tell me about that.

**Diego:** We support 2FA and we strongly recommend it, but it's not mandatory. Users can enable it under "Mi Perfil" > "Seguridad" > "Autenticacion en Dos Pasos".

When enabled, every login requires:
1. Email and password (as usual)
2. A 6-digit code sent via SMS to their registered phone number

The code expires after 5 minutes. If they don't receive it, they can request a new one (with a 60-second cooldown between requests).

The bot should encourage users to enable 2FA: "Te recomendamos activar la autenticacion en dos pasos para mayor seguridad de tu cuenta. Puedes hacerlo en Mi Perfil > Seguridad." (We recommend enabling two-factor authentication for better account security. You can do this in My Profile > Security.)

**You:** Now let's get into troubleshooting. What are the most common issues users report?

**Diego:** Oh boy. Alright, here are the top issues and what the bot should recommend:

### 1. App crashing / closing unexpectedly

This is the most common complaint. Almost always user-side. Steps to suggest:

1. **Clear the app cache**: Go to phone settings > Apps > Emporyum Tech > Clear Cache. This resolves about 60% of crash issues.
2. **Update to the latest version**: Check the App Store / Play Store for updates. We push bug fixes regularly.
3. **Restart the phone**: The classic IT solution, but it works. Especially on Android devices with limited RAM.
4. **Reinstall the app**: If nothing else works, delete and reinstall. Their account data is not lost - it's all server-side.

Bot response: "Si la app se cierra inesperadamente, intenta estos pasos: 1) Limpia el cache de la app en los ajustes de tu telefono, 2) Actualiza la app a la ultima version, 3) Reinicia tu telefono, 4) Si el problema persiste, desinstala y vuelve a instalar la app. Tus datos no se perderan."

### 2. Login issues / can't sign in

Common causes and solutions:

- **Wrong password**: Suggest password reset (the flow I described above)
- **Wrong email**: Users sometimes forget which email they used. Suggest trying variations (personal vs work email). If they really can't remember, escalate to support.
- **Account locked**: See security section below. If they see "cuenta bloqueada" (account locked), they need support.
- **App not loading login screen**: Could be internet connection. Check wifi/data.

Bot response: "Si no puedes iniciar sesion, verifica que tu correo y contrasena sean correctos. Si olvidaste tu contrasena, puedes restablecerla desde la pantalla de inicio de sesion. Si tu cuenta esta bloqueada, contacta a nuestro equipo de soporte."

### 3. Notifications not working

Users say "no me llegan las notificaciones" (I don't get notifications):

1. **Check phone notification settings**: Settings > Notifications > Emporyum Tech > make sure they're enabled
2. **Check in-app notification settings**: Mi Perfil > Notificaciones > make sure the relevant types are toggled on
3. **Battery optimization**: On Android, some manufacturers (Samsung, Huawei, Xiaomi) have aggressive battery optimization that kills background processes. They need to exclude Emporyum Tech from battery optimization.
4. **Do Not Disturb**: Check if DND is on

Bot response: "Si no recibes notificaciones, verifica: 1) En los ajustes de tu telefono que las notificaciones de Emporyum Tech esten habilitadas, 2) En la app, en Mi Perfil > Notificaciones, que los tipos de notificacion esten activados. En Android, tambien verifica que la app no este restringida por el ahorro de bateria."

### 4. App running slow

- **Check internet connection**: Try switching between wifi and mobile data
- **Close other apps**: Free up phone memory
- **Clear cache**: Same as for crashes
- **Update the app**: Performance improvements are included in updates

Bot response: "Si la app esta lenta, verifica tu conexion a internet, cierra otras apps que no estes usando, y limpia el cache de Emporyum Tech. Tambien asegurate de tener la ultima version de la app."

### 5. "My order doesn't appear" / order not showing

This one is interesting. There's usually a short delay between completing a purchase and the order appearing in "Mis Pedidos":

- **Wait 5 minutes**: There's a processing delay, especially during peak hours
- **Force-refresh**: Pull down on the "Mis Pedidos" screen to refresh
- **Check email**: If they received a confirmation email, the order exists - it might just take a moment to sync to the app
- **Check for Efecty/A la Mano**: If they chose one of these payment methods, the order won't fully appear until payment is confirmed

Bot response: "Si tu pedido no aparece en Mis Pedidos, espera unos 5 minutos y actualiza la pantalla deslizando hacia abajo. Si pagaste por Efecty o Bancolombia A la Mano, el pedido aparecera una vez se confirme tu pago. Si ya paso mas tiempo y aun no aparece, contacta a soporte."

**You:** Great. Let's talk about security - what should the bot know?

**Diego:** Security is critical. Here are the main scenarios:

### Suspicious activity / account locked

Our fraud detection system monitors for unusual behavior: login from a new device in a different country, multiple failed login attempts, unusual purchase patterns. When triggered:

- The account is **locked automatically**
- The user receives an email and SMS notification
- They cannot make purchases or change account settings
- To unlock: they must contact support, verify their identity (full name, ID number, registered phone), and the support agent will review the activity and unlock if appropriate

The bot should say: "Tu cuenta ha sido bloqueada por actividad sospechosa. Para desbloquearla, contacta a nuestro equipo de soporte. Por seguridad, necesitaras verificar tu identidad." (Your account has been locked due to suspicious activity. To unlock it, contact our support team. For security, you'll need to verify your identity.)

### OTP / verification code safety

This is really important: the bot should NEVER ask for OTP codes. And it should warn users to never share them. If a user volunteers their OTP in the chat, the bot should immediately say: "Nunca compartas tu codigo de verificacion con nadie, incluyendo nuestro equipo de soporte. Si alguien te pide tu codigo, es un intento de fraude." (Never share your verification code with anyone, including our support team. If someone asks for your code, it's a fraud attempt.)

### Phishing awareness

The bot should warn users about phishing if they mention receiving suspicious emails or messages. Key points:

- Emporyum Tech will never ask for your password via email or chat
- Emporyum Tech will never ask for your full card number
- Official emails come from @emporyumtech.com only
- If in doubt, don't click links - go directly to the app

Bot response: "Emporyum Tech nunca te pedira tu contrasena, codigo de verificacion o numero completo de tarjeta por correo o chat. Si recibes un mensaje sospechoso, no hagas clic en ningun enlace y reportalo a seguridad@emporyumtech.com."

**You:** What about account deletion and recovery?

**Diego:** Account deletion is available under "Mi Perfil" > "Eliminar Cuenta". When a user deletes their account:

- All personal data is scheduled for deletion (GDPR compliance, even though it's Colombia we follow similar standards with Habeas Data)
- Active orders continue to be processed (we don't cancel orders because of account deletion)
- Outstanding payment obligations remain (deleting your account doesn't erase your debt)
- **Recovery is possible within 30 days**: If the user changes their mind, they can contact support to restore their account. After 30 days, the data is permanently deleted and the account cannot be recovered.

The bot should explain this clearly: "Puedes eliminar tu cuenta en Mi Perfil > Eliminar Cuenta. Tienes 30 dias para recuperarla contactando a soporte. Despues de ese plazo, la eliminacion es permanente. Ten en cuenta que las obligaciones de pago pendientes se mantienen." (You can delete your account in My Profile > Delete Account. You have 30 days to recover it by contacting support. After that period, the deletion is permanent. Note that outstanding payment obligations remain.)

### Account merge

Sometimes users accidentally create two accounts (maybe one with personal email, one with work email). We do NOT support self-service account merge. This requires human support to verify both accounts belong to the same person and manually consolidate the data.

Bot response: "La fusion de cuentas no esta disponible de forma automatica. Contacta a nuestro equipo de soporte con los datos de ambas cuentas para que puedan gestionar la unificacion." (Account merging is not available automatically. Contact our support team with the details of both accounts so they can manage the unification.)

### API rate limits - DO NOT MENTION TO USERS

We have rate limits on our APIs to prevent abuse. The bot should NEVER mention these to users. If a user hits a rate limit (which would manifest as "something went wrong" errors), the bot should just suggest trying again in a few minutes. No technical explanations.

**You:** Any other platform-related things the bot should handle?

**Diego:** Let me think...

Oh, there's the **app permissions** thing. Users sometimes ask why the app needs certain permissions:

- **Camera**: For scanning QR codes for payments and uploading product photos for returns
- **Location**: For finding nearby Efecty payment points
- **Notifications**: For payment reminders and order updates
- **Storage**: For downloading receipts and invoices

The bot can explain these if asked: "La app solicita estos permisos para ofrecerte una mejor experiencia: la camara se usa para escanear codigos QR y subir fotos, la ubicacion para encontrar puntos de pago cercanos, y las notificaciones para recordatorios de pago." (The app requests these permissions to offer you a better experience: the camera is used for scanning QR codes and uploading photos, location for finding nearby payment points, and notifications for payment reminders.)

Also - **app version check**. Users should be on the latest version. They can check their current version in "Mi Perfil" > "Acerca de" (About). If they're on an old version (more than 3 months old), the bot should strongly recommend updating.

And one more edge case: sometimes users are on a **really old phone** that can't run the latest app version. In that case, they should use the web version at emporyumtech.com instead. The bot should suggest this as a fallback.

**You:** Perfect. Thanks, Diego.

**Diego:** No worries. One parting thought: the bot should always try to solve things within the app first before suggesting they contact support. The whole point is reducing support tickets. If the bot's answer is always "contacta a soporte," we haven't really improved anything. Solve what you can, escalate only what you must.

---

## Key Information Summary

_(For interviewer reference - candidates should extract this themselves)_

### Topics to Extract
- **MI CUENTA**: Account management - what users can/can't change, password reset flow, 2FA, account deletion/recovery, account merge (escalate). Legal name and ID number changes require support tickets.
- **COMO FUNCIONA LA APP**: App features, platform availability (iOS, Android, Web), troubleshooting for common issues (crashes, login, notifications, slow app, missing orders). Security (locked accounts, OTP safety, phishing). App permissions explanation.

### Response Language
All bot responses should be in **Spanish** since the bot serves Colombian users.

### Edge Cases
- Account locked: escalate to support with identity verification
- OTP: never ask for it, warn users not to share
- Deleted accounts: 30-day recovery window
- Account merge: human support only
- API rate limits: never mention to users
- Old phones: suggest web version as fallback
- Always try in-app solutions before escalating
