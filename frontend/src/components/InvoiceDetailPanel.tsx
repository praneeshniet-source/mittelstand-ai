
import { AlertCircle, CalendarDays, CheckCircle2, FileText, MapPin, X } from 'lucide-react'

export type InvoiceDetail = {
  invoice_id: string
  supplier: string
  country: string | null
  category: string | null
  invoice_date: string
  due_date: string
  amount_eur: number
  status: string
  is_overdue: boolean
}

type InvoiceDetailPanelProps = {
  invoice: InvoiceDetail
  onClose: () => void
  currency: (value: number) => string
  formatDate: (value: string) => string
}

export default function InvoiceDetailPanel({
  invoice,
  onClose,
  currency,
  formatDate,
}: InvoiceDetailPanelProps) {
  const isPaid = invoice.status.toLowerCase() === 'paid'

  const statusLabel = invoice.is_overdue
    ? 'Overdue'
    : isPaid
      ? 'Paid'
      : 'Unpaid'

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-slate-950/40"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby="invoice-detail-title"
        className="flex h-full w-full max-w-lg flex-col overflow-y-auto bg-white shadow-2xl"
      >
        <header className="flex items-center justify-between border-b border-slate-200 p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
              <FileText size={20} />
            </div>
            <div>
              <h2
                id="invoice-detail-title"
                className="font-semibold text-slate-900"
              >
                Invoice details
              </h2>
              <p className="text-xs text-slate-400">
                {invoice.invoice_id}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close invoice details"
            className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100"
          >
            <X size={19} />
          </button>
        </header>

        <div className="flex-1 space-y-6 p-5">
          <section>
            <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
              Supplier
            </p>
            <h3 className="mt-2 text-xl font-semibold text-slate-900">
              {invoice.supplier}
            </h3>
            <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
              {invoice.country && (
                <span className="flex items-center gap-1">
                  <MapPin size={13} />
                  {invoice.country}
                </span>
              )}
              {invoice.category && (
                <span>{invoice.category}</span>
              )}
            </div>
          </section>

          <section className="rounded-xl border border-slate-200 p-4">
            <p className="text-xs text-slate-500">Invoice amount</p>
            <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">
              {currency(invoice.amount_eur)}
            </p>

            <span
              className={`mt-4 inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium ${
                invoice.is_overdue
                  ? 'bg-red-50 text-red-700'
                  : isPaid
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'bg-amber-50 text-amber-700'
              }`}
            >
              {invoice.is_overdue ? (
                <AlertCircle size={14} />
              ) : isPaid ? (
                <CheckCircle2 size={14} />
              ) : (
                <AlertCircle size={14} />
              )}
              {statusLabel}
            </span>
          </section>

          <section className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-900">
              Invoice timeline
            </h3>

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-blue-50 p-2 text-blue-600">
                <CalendarDays size={17} />
              </div>
              <div>
                <p className="text-xs text-slate-400">Invoice date</p>
                <p className="mt-1 text-sm font-medium text-slate-800">
                  {formatDate(invoice.invoice_date)}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div
                className={`rounded-lg p-2 ${
                  invoice.is_overdue
                    ? 'bg-red-50 text-red-600'
                    : 'bg-slate-100 text-slate-600'
                }`}
              >
                <CalendarDays size={17} />
              </div>
              <div>
                <p className="text-xs text-slate-400">Payment due date</p>
                <p
                  className={`mt-1 text-sm font-medium ${
                    invoice.is_overdue
                      ? 'text-red-600'
                      : 'text-slate-800'
                  }`}
                >
                  {formatDate(invoice.due_date)}
                </p>
              </div>
            </div>
          </section>

          {invoice.is_overdue && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-red-700">
                <AlertCircle size={17} />
                Payment overdue
              </div>
              <p className="mt-2 text-xs leading-5 text-red-600">
                This invoice was unpaid on the reporting date. Follow up with
                the supplier or review the payment status.
              </p>
            </div>
          )}
        </div>

        <footer className="border-t border-slate-200 p-5">
          <button
            type="button"
            onClick={onClose}
            className="w-full rounded-lg bg-slate-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
          >
            Close details
          </button>
        </footer>
      </aside>
    </div>
  )
}
