# Checkout Pending Order Design

## Goal

Add a dedicated light-theme checkout confirmation page for paid plans. After a
user selects a plan, they provide basic contact details, confirm the order, and
are redirected to the Z-Pay QR-code payment page only after a pending order is
created.

## Scope

- Add a dedicated checkout route reached from the paid plan buttons.
- Carry the selected plan identifier from the pricing page to checkout.
- Show a two-column desktop layout: customer information on the left and an
  order summary card on the right.
- Collect name, mobile number, email, and agreement confirmation.
- Validate all required fields before the confirmation request.
- Create a pending order before redirecting to the Z-Pay payment page.
- Preserve form values and show an actionable error when order creation fails.
- Use a responsive single-column mobile layout with the order summary before
  the form and a persistent confirmation action.

## Out of Scope

- Invoice fields or invoice processing.
- Card, wallet, or other embedded payment methods.
- Editing prices, periods, or plan entitlements from checkout.
- Payment status polling or order-history UI beyond the redirect target.

## User Flow

1. The user chooses a paid plan on `/pricing`.
2. The pricing CTA navigates to `/checkout?plan=<plan-id>`.
3. Checkout resolves the plan from a local, trusted plan catalog. Missing or
   invalid plans return the user to `/pricing`.
4. The user completes name, mobile number, email, and the agreement checkbox.
5. Selecting `Confirm Order` validates the form and creates an order with
   `pending_payment` status.
6. A successful response redirects to the Z-Pay QR-code page using the payment
   URL or order reference supplied by the backend.
7. A failed request keeps the form and plan summary visible, then shows the
   failure message above the form.

## Page Design

### Desktop

- Use the existing day-theme palette: white surfaces, dark ink text, and the
  muted blue-gray accent used by pricing cards.
- Keep a compact top bar with a back action labeled `Back to plans`.
- Use a content grid with a flexible form column and a 380px order-summary
  column.
- Keep the summary card sticky within the checkout content area.
- The form uses simple labels and high-contrast, full-width inputs. No invoice
  or payment-card controls are shown.
- The order card contains plan name, billing period, plan benefits, subtotal,
  discount when applicable, total amount, and the confirmation button.
- Show the plan data as read-only. A secondary link returns to pricing to
  change the plan.

### Mobile

- Collapse to a single column below the tablet breakpoint.
- Render the order summary before the form so total cost is visible before data
  entry.
- Keep the primary confirmation button reachable with a sticky bottom action
  area while the user completes the form.
- Use no horizontal scrolling and retain at least 44px tap targets.

## Components and Data Boundaries

- `Pricing.vue` owns plan selection and routes with the canonical plan ID.
- `Checkout.vue` owns form state, client-side validation, pending-order
  submission, and navigation to payment.
- A shared plan catalog is the single source for plan name, price, period, and
  benefits used by both pricing and checkout.
- `orderClient.ts` owns the API request for creating a pending order and
  exposes a typed response containing the order reference and Z-Pay URL.
- The backend is authoritative for final price calculation and payment URL
  generation. The frontend catalog is display-only.

## States and Error Handling

- Invalid plan: show a short notice and return to `/pricing`.
- Invalid form: show inline field errors and focus the first invalid control.
- Agreement unchecked: block submission with an inline error.
- Submission in progress: disable the confirmation action and show a concise
  pending state to prevent duplicate orders.
- Order creation failure: retain input and show a retryable error without
  changing the selected plan.
- Successful order creation: navigate directly to the Z-Pay QR-code page.

## Verification

- Build passes TypeScript and Vite validation.
- Pricing CTAs for every paid plan produce the expected checkout URL.
- Checkout shows the matching plan, amount, period, and benefits.
- Required-field, invalid email, and unchecked-agreement cases block
  submission.
- A successful mocked pending-order response redirects to the returned Z-Pay
  URL.
- A failed mocked response preserves form input and exposes an error message.
- Desktop and mobile screenshots confirm the two-column and single-column
  layouts without overflow.
