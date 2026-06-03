# POS Payment - Invoice Payment Module

This module extends Odoo 18 Point of Sale to allow registering payments for unpaid customer invoices directly from the POS interface.

## Features

- **Invoice Button**: Adds an "Invoice" button in the POS product screen (replaces first Internal Note button)
- **Invoice List**: Shows all unpaid invoices, filtered by selected customer if any
- **Multiple Selection**: Select one or multiple invoices for payment
- **Payment Registration**: Register payments with journal selection and amount specification
- **Automatic Reconciliation**: Automatically reconciles payments with selected invoices

## Installation

1. Copy the `pos_payment` folder to your Odoo addons directory
2. Update the apps list in Odoo
3. Install the "POS Payment - Invoice Payment" module

## Configuration

1. Go to Point of Sale → Configuration → Point of Sale
2. Select your POS configuration
3. In the "Accounting" tab:
   - Enable "Enable Invoice Payment"
   - Select payment journals to use for invoice payments (optional)

## Usage

### In POS:

1. Open a POS session
2. Click on the "Actions" button (three dots)
3. Click on "Invoice" button
4. The invoice list popup will show:
   - If a customer is selected: Only that customer's unpaid invoices
   - If no customer is selected: All unpaid invoices
5. Select one or multiple invoices by clicking on them
6. Click "Register Payment"
7. In the payment popup:
   - Select a payment journal
   - Enter the payment amount (defaults to total of selected invoices)
   - Click "Apply Payment"
8. Payment will be created and automatically reconciled with the invoices

## Technical Details

### Python Models

- **pos.config**: Added fields for invoice payment configuration
- **pos.session**: Added methods for fetching invoices and registering payments
- **account.move**: Extended with POS data loading mixins
- **account.journal**: Extended with POS data loading mixins

### JavaScript Components

- **ControlButtons**: Patched to add Invoice button
- **InvoiceListPopup**: Shows list of unpaid invoices with selection
- **PaymentRegisterPopup**: Handles payment registration
- **PosStore**: Added methods for invoice operations

### API Methods

#### `_get_pos_ui_account_move(params)`
Fetches unpaid invoices with optional filtering:
- `partner_id`: Filter by partner (child_of)
- `currency_id`: Filter by currency
- `limit`: Maximum number of invoices (default: 100)

#### `_register_invoice_payment(invoice_ids, journal_id, amount)`
Creates and posts a payment, then reconciles with selected invoices:
- `invoice_ids`: List of invoice IDs to pay
- `journal_id`: Payment journal to use
- `amount`: Payment amount

## Dependencies

- `point_of_sale`
- `account`

## Version

- Odoo: 18.0
- Module: 1.0.0

## License

LGPL-3

## Author

Optin Developer

## Support

For issues or feature requests, please contact your Odoo administrator.
