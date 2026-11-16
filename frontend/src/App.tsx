
import { useEffect, useState, type FormEvent } from 'react'
import {
  Activity,
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  BrainCircuit,
  Building2,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  FileText,
  LayoutDashboard,
  LoaderCircle,
  MessageSquare,
  Search,
  Send,
  Settings,
  ShieldCheck,
  Sparkles,
  Wallet,
  X,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import InvoiceDetailPanel from './components/InvoiceDetailPanel'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

type Portfolio = {
  invoice_count: number
  total_value: number
  paid: number
  unpaid: number
  overdue: number
  not_due: number
  overdue_invoice_count: number
  not_due_invoice_count: number
}

type Invoice = {
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

type InvoiceResponse = {
  invoices: Invoice[]
  pagination: {
    page: number
    page_size: number
    total_records: number
    total_pages: number
  }
  reporting_date: string
}

type AssistantMessage = {
  role: 'user' | 'assistant'
  content: string
}

type SortField = 'due_date' | 'invoice_date' | 'amount_eur'

const currency = (value: number) =>
  new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(value)

const formatDate = (value: string) =>
  new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(`${value}T00:00:00Z`))

function App() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [loading, setLoading] = useState(true)
  const [apiError, setApiError] = useState('')
  const [apiConnected, setApiConnected] = useState(false)

  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null)
  const [invoiceLoading, setInvoiceLoading] = useState(true)
  const [invoiceError, setInvoiceError] = useState('')
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('all')
  const [overdueOnly, setOverdueOnly] = useState(false)
  const [sortBy, setSortBy] = useState<SortField>('due_date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  const [page, setPage] = useState(1)
  const [pageSize] = useState(5)
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 5,
    total_records: 0,
    total_pages: 0,
  })

  const [question, setQuestion] = useState('')

  const [messages, setMessages] = useState<AssistantMessage[]>([
    {
      role: 'assistant',
      content: `Guten Morgen! I'm POKO. 👋 I'm your intelligent financial operations companion. Ask me about overdue invoices, outstanding payments, supplier risks, or business workflows.`,
    },
  ])

  const [asking, setAsking] = useState(false)

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setLoading(true)
        setApiError('')

        const healthResponse = await fetch(`${API_BASE_URL}/health`)
        if (!healthResponse.ok) {
          throw new Error('Backend health check failed.')
        }

        setApiConnected(true)

        const response = await fetch(`${API_BASE_URL}/analytics/overview`)
        if (!response.ok) {
          throw new Error(
            response.status === 404
              ? 'No portfolio data was returned by the backend.'
              : 'Could not load financial portfolio data.',
          )
        }

        const data: Portfolio = await response.json()
        setPortfolio(data)
      } catch (error) {
        setApiConnected(false)
        setApiError(
          error instanceof Error
            ? error.message
            : 'Unable to connect to the backend.',
        )
      } finally {
        setLoading(false)
      }
    }

    loadDashboard()
  }, [])

  useEffect(() => {
    const controller = new AbortController()

    const loadInvoices = async () => {
      try {
        setInvoiceLoading(true)
        setInvoiceError('')

        const params = new URLSearchParams({
          page: String(page),
          page_size: String(pageSize),
          sort_by: sortBy,
          sort_order: sortOrder,
        })

        if (search.trim()) params.set('search', search.trim())
        if (status !== 'all') params.set('status', status)
        if (overdueOnly) params.set('overdue_only', 'true')

        const response = await fetch(
          `${API_BASE_URL}/invoices?${params.toString()}`,
          { signal: controller.signal },
        )

        if (!response.ok) {
          throw new Error(
            `Could not load invoices. Server returned ${response.status}.`,
          )
        }

        const data: InvoiceResponse = await response.json()

        setInvoices(data.invoices)
        setPagination(data.pagination)
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return

        setInvoiceError(
          error instanceof Error
            ? error.message
            : 'Unable to load invoices.',
        )
        setInvoices([])
      } finally {
        if (!controller.signal.aborted) {
          setInvoiceLoading(false)
        }
      }
    }

    loadInvoices()

    return () => controller.abort()
  }, [search, status, overdueOnly, sortBy, sortOrder, page, pageSize])

  const askAssistant = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || asking) return

    setMessages((previous) => [
      ...previous,
      { role: 'user', content: trimmedQuestion },
    ])
    setQuestion('')
    setAsking(true)

    try {
      const response = await fetch(`${API_BASE_URL}/ai/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: trimmedQuestion,
          top_k: 3,
        }),
      })

      if (!response.ok) {
        throw new Error('The assistant could not process your question.')
      }

      const data = await response.json()

      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          content: data.answer || 'The assistant returned no answer.',
        },
      ])
    } catch (error) {
      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          content:
            error instanceof Error
              ? error.message
              : 'Unable to reach the AI service.',
        },
      ])
    } finally {
      setAsking(false)
    }
  }

  const resetFilters = () => {
    setSearch('')
    setStatus('all')
    setOverdueOnly(false)
    setSortBy('due_date')
    setSortOrder('asc')
    setPage(1)
  }

  const chartData = portfolio
    ? [
        { name: 'Paid', amount: portfolio.paid },
        { name: 'Unpaid', amount: portfolio.unpaid },
        { name: 'Overdue', amount: portfolio.overdue },
        { name: 'Not due', amount: portfolio.not_due },
      ]
    : []

  const pieData = portfolio
    ? [
        { name: 'Paid', value: portfolio.paid },
        { name: 'Outstanding', value: portfolio.unpaid },
      ]
    : []

  const metrics = [
    {
      label: 'Total invoice value',
      value: portfolio ? currency(portfolio.total_value) : '—',
      icon: Wallet,
      description: 'Across the invoice portfolio',
    },
    {
      label: 'Paid',
      value: portfolio ? currency(portfolio.paid) : '—',
      icon: CheckCircle2,
      description: 'Successfully paid invoices',
    },
    {
      label: 'Outstanding',
      value: portfolio ? currency(portfolio.unpaid) : '—',
      icon: ArrowUpRight,
      description: 'Unpaid invoice value',
    },
    {
      label: 'Overdue',
      value: portfolio ? currency(portfolio.overdue) : '—',
      icon: AlertCircle,
      description: `${portfolio?.overdue_invoice_count ?? '—'} overdue invoices`,
    },
  ]

  return (
    <div className="min-h-screen bg-[#f5f7fb] text-slate-800">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-[250px] flex-col bg-[#111c32] text-white lg:flex">
        <div className="flex h-[76px] items-center gap-3 border-b border-white/10 px-6">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500">
            <BrainCircuit size={21} />
          </div>

          <div>
            <h1 className="text-[15px] font-semibold tracking-wide">
              Mittelstand AI
            </h1>
            <p className="text-[10px] tracking-[2px] text-slate-400">
              FINANCE INTELLIGENCE
            </p>
          </div>
        </div>

        <div className="px-4 pt-7">
          <p className="mb-3 px-3 text-[10px] font-semibold tracking-[2px] text-slate-500">
            WORKSPACE
          </p>

          <nav className="space-y-1" aria-label="Main workspace navigation">
            <a
              href="#overview"
              className="flex items-center gap-3 rounded-lg bg-blue-500/15 px-3 py-3 text-sm font-medium text-blue-300"
            >
              <LayoutDashboard size={18} />
              Overview
            </a>

            <a
              href="#invoice-explorer"
              className="flex items-center gap-3 rounded-lg px-3 py-3 text-sm text-slate-400 transition hover:bg-white/5 hover:text-white"
            >
              <FileText size={18} />
              Invoices
            </a>

            <a className="flex items-center gap-3 rounded-lg px-3 py-3 text-sm text-slate-400 transition hover:bg-white/5 hover:text-white">
              <Building2 size={18} />
              Suppliers
            </a>

            <a
              href="#ai-assistant"
              className="flex items-center gap-3 rounded-lg px-3 py-3 text-sm text-slate-400 transition hover:bg-white/5 hover:text-white"
            >
              <MessageSquare size={18} />
              AI Assistant
            </a>
          </nav>
        </div>

        <div className="mt-auto border-t border-white/10 p-4">
          <a className="flex items-center gap-3 rounded-lg px-3 py-3 text-sm text-slate-400 hover:bg-white/5 hover:text-white">
            <Settings size={18} />
            Settings
          </a>

          <div className="mt-4 flex items-center gap-3 rounded-xl bg-white/5 p-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-600 text-xs font-semibold">
              PA
            </div>

            <div className="min-w-0">
              <p className="text-xs font-medium">Finance workspace</p>
              <p className="text-[10px] text-slate-400">Administrator</p>
            </div>

            <ChevronDown className="ml-auto text-slate-400" size={15} />
          </div>
        </div>
      </aside>

      <main className="min-h-screen min-w-0 lg:ml-[250px]">
        {/* Top header */}
        <header className="flex min-h-[76px] flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-3 sm:px-8">
          <div>
            <p className="text-xs text-slate-400">Workspace / Overview</p>
            <h2 className="mt-1 text-lg font-semibold text-slate-900">
              Financial overview
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-2 text-xs">
              <span
                className={`h-2 w-2 rounded-full ${
                  apiConnected ? 'bg-emerald-500' : 'bg-amber-500'
                }`}
              />

              <span className="text-slate-600">
                <span className="sm:hidden">API</span>
                <span className="hidden sm:inline">
                  {apiConnected ? 'Backend connected' : 'Backend unavailable'}
                </span>
              </span>
            </div>

            <button
              type="button"
              aria-label="Help"
              className="hidden rounded-full border border-slate-200 p-2 text-slate-500 sm:block"
            >
              <CircleHelp size={17} />
            </button>
          </div>
        </header>

        {/* Mobile navigation */}
        <nav
          aria-label="Mobile workspace navigation"
          className="flex items-center gap-2 overflow-x-auto border-b border-slate-200 bg-white px-4 py-2 lg:hidden"
        >
          <a
            href="#overview"
            className="min-h-10 shrink-0 rounded-lg bg-blue-50 px-3 py-2.5 text-xs font-medium text-blue-700"
          >
            Overview
          </a>

          <a
            href="#invoice-explorer"
            className="min-h-10 shrink-0 rounded-lg px-3 py-2.5 text-xs font-medium text-slate-600 transition hover:bg-slate-100"
          >
            Invoices
          </a>

          <a
            href="#ai-assistant"
            className="min-h-10 shrink-0 rounded-lg px-3 py-2.5 text-xs font-medium text-slate-600 transition hover:bg-slate-100"
          >
            POKO
          </a>
        </nav>

        <div className="mx-auto max-w-[1500px] min-w-0 space-y-5 p-4 sm:space-y-6 sm:p-6 lg:p-8">
          {/* Dashboard heading */}
          <section
            id="overview"
            className="flex scroll-mt-6 flex-col justify-between gap-3 sm:flex-row sm:items-end"
          >
            <div>
              <p className="text-sm text-slate-500">
                Financial intelligence at a glance
              </p>

              <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">
                Dashboard
              </h2>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Activity size={15} />
              Live data from your financial backend
            </div>
          </section>

          {/* Dashboard error */}
          {apiError && (
            <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
              <AlertCircle className="mt-0.5 shrink-0" size={18} />

              <div>
                <p className="font-semibold">Financial data unavailable</p>
                <p className="mt-1">{apiError}</p>
                <p className="mt-1 text-xs">
                  Check that the FastAPI server is running and that the
                  dashboard can reach it.
                </p>
              </div>
            </div>
          )}

          {/* KPI cards */}
          <section className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
            {metrics.map((metric) => {
              const Icon = metric.icon

              return (
                <article
                  key={metric.label}
                  className="min-w-0 rounded-xl border border-slate-200 bg-white p-3 shadow-sm sm:p-5"
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs font-medium text-slate-500">
                      {metric.label}
                    </p>

                    <div className="shrink-0 rounded-lg bg-slate-100 p-2 text-slate-600">
                      <Icon size={17} />
                    </div>
                  </div>

                  <div className="mt-3 min-h-9 break-words text-xl font-semibold tracking-tight text-slate-900 sm:mt-4 sm:text-[25px]">
                    {loading ? (
                      <LoaderCircle
                        className="animate-spin text-slate-400"
                        size={22}
                      />
                    ) : (
                      metric.value
                    )}
                  </div>

                  <p className="mt-2 text-[11px] leading-4 text-slate-400">
                    {metric.description}
                  </p>
                </article>
              )
            })}
          </section>

          {/* Portfolio charts */}
          <section className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
            <article className="min-w-0 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="font-semibold text-slate-900">
                    Invoice portfolio
                  </h3>

                  <p className="mt-1 text-xs text-slate-400">
                    Financial distribution by payment status
                  </p>
                </div>

                <span className="shrink-0 rounded-lg bg-slate-100 px-3 py-2 text-[11px] text-slate-600">
                  EUR
                </span>
              </div>

              <div className="mt-5 h-[230px] min-w-0 sm:mt-6 sm:h-[260px]">
                {loading ? (
                  <div className="flex h-full items-center justify-center text-sm text-slate-400">
                    <LoaderCircle className="mr-2 animate-spin" size={18} />
                    Loading portfolio...
                  </div>
                ) : portfolio ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={chartData}
                      margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        vertical={false}
                        stroke="#edf0f5"
                      />

                      <XAxis
                        dataKey="name"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#94a3b8', fontSize: 11 }}
                        dy={10}
                      />

                      <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#94a3b8', fontSize: 10 }}
                        tickFormatter={(value: number) =>
                          `€${value.toLocaleString('en-GB')}`
                        }
                        width={75}
                      />

                      <Tooltip
                        formatter={(value) => [
                          currency(Number(value)),
                          'Amount',
                        ]}
                        contentStyle={{
                          borderRadius: 10,
                          border: '1px solid #e2e8f0',
                          fontSize: 12,
                        }}
                      />

                      <Bar
                        dataKey="amount"
                        fill="#4778d9"
                        radius={[5, 5, 0, 0]}
                        maxBarSize={55}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-slate-400">
                    Portfolio chart will appear when data is available.
                  </div>
                )}
              </div>
            </article>

            <article className="min-w-0 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
              <h3 className="font-semibold text-slate-900">
                Payment composition
              </h3>

              <p className="mt-1 text-xs text-slate-400">
                Paid versus outstanding invoice value
              </p>

              <div className="relative mt-3 h-[190px] min-w-0 sm:h-[205px]">
                {loading ? (
                  <div className="flex h-full items-center justify-center text-sm text-slate-400">
                    <LoaderCircle className="mr-2 animate-spin" size={18} />
                    Loading...
                  </div>
                ) : portfolio ? (
                  <>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={pieData}
                          dataKey="value"
                          nameKey="name"
                          innerRadius={62}
                          outerRadius={86}
                          paddingAngle={4}
                          stroke="none"
                        >
                          <Cell fill="#4778d9" />
                          <Cell fill="#f0a34a" />
                        </Pie>

                        <Tooltip
                          formatter={(value) => currency(Number(value))}
                        />
                      </PieChart>
                    </ResponsiveContainer>

                    <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                      <p className="text-[10px] text-slate-400">Invoices</p>
                      <p className="text-2xl font-semibold text-slate-900">
                        {portfolio.invoice_count}
                      </p>
                    </div>
                  </>
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-slate-400">
                    No portfolio data available.
                  </div>
                )}
              </div>

              <div className="mt-2 space-y-3">
                <div className="flex items-center justify-between gap-2 text-xs">
                  <span className="flex items-center gap-2 text-slate-500">
                    <span className="h-2.5 w-2.5 rounded-full bg-[#4778d9]" />
                    Paid
                  </span>

                  <strong className="text-right text-slate-800">
                    {portfolio ? currency(portfolio.paid) : '—'}
                  </strong>
                </div>

                <div className="flex items-center justify-between gap-2 text-xs">
                  <span className="flex items-center gap-2 text-slate-500">
                    <span className="h-2.5 w-2.5 rounded-full bg-[#f0a34a]" />
                    Outstanding
                  </span>

                  <strong className="text-right text-slate-800">
                    {portfolio ? currency(portfolio.unpaid) : '—'}
                  </strong>
                </div>
              </div>
            </article>
          </section>

          {/* Invoice explorer */}
          <section
            id="invoice-explorer"
            className="scroll-mt-6 min-w-0 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6"
          >
            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">
                  Invoice Explorer
                </h3>

                <p className="mt-1 text-xs text-slate-400">
                  Search, filter and inspect supplier invoices
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs text-slate-500">
                <FileText size={15} />
                <span>{pagination.total_records} matching invoices</span>
              </div>
            </div>

            {/* Invoice filters */}
            <div className="mt-5 grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-[minmax(220px,1.5fr)_minmax(130px,0.7fr)_minmax(160px,0.8fr)_auto]">
              <div className="relative min-w-0">
                <Search
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                  size={16}
                />

                <input
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value)
                    setPage(1)
                  }}
                  placeholder="Search invoice ID or supplier..."
                  aria-label="Search invoices"
                  className="min-h-11 w-full min-w-0 rounded-lg border border-slate-200 bg-white py-2.5 pl-9 pr-9 text-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                />

                {search && (
                  <button
                    type="button"
                    onClick={() => {
                      setSearch('')
                      setPage(1)
                    }}
                    aria-label="Clear search"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
                  >
                    <X size={15} />
                  </button>
                )}
              </div>

              <select
                value={status}
                onChange={(event) => {
                  setStatus(event.target.value)
                  setPage(1)
                }}
                aria-label="Filter by payment status"
                className="min-h-11 w-full min-w-0 rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-blue-400"
              >
                <option value="all">All statuses</option>
                <option value="Paid">Paid</option>
                <option value="Unpaid">Unpaid</option>
              </select>

              <select
                value={`${sortBy}:${sortOrder}`}
                onChange={(event) => {
                  const [field, order] = event.target.value.split(':')
                  setSortBy(field as SortField)
                  setSortOrder(order as 'asc' | 'desc')
                  setPage(1)
                }}
                aria-label="Sort invoices"
                className="min-h-11 w-full min-w-0 rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-blue-400"
              >
                <option value="due_date:asc">Due date: earliest first</option>
                <option value="due_date:desc">Due date: latest first</option>
                <option value="invoice_date:desc">Invoice date: newest</option>
                <option value="invoice_date:asc">Invoice date: oldest</option>
                <option value="amount_eur:desc">Amount: highest first</option>
                <option value="amount_eur:asc">Amount: lowest first</option>
              </select>

              <button
                type="button"
                onClick={resetFilters}
                className="flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border border-slate-200 px-4 py-2.5 text-sm text-slate-600 transition hover:bg-slate-50 xl:w-auto"
              >
                <X size={15} />
                Reset
              </button>
            </div>

            {/* Overdue filter */}
            <div className="mt-3 flex flex-col items-start justify-between gap-3 sm:flex-row sm:flex-wrap sm:items-center">
              <label className="flex min-h-10 cursor-pointer items-center gap-2 text-xs text-slate-600">
                <input
                  type="checkbox"
                  checked={overdueOnly}
                  onChange={(event) => {
                    setOverdueOnly(event.target.checked)
                    setPage(1)
                  }}
                  className="h-4 w-4 rounded border-slate-300 accent-blue-600"
                />
                Show overdue invoices only
              </label>

              <p className="text-[11px] text-slate-400">
                Reporting date: 27 Oct 2026
              </p>
            </div>

            {invoiceError && (
              <div className="mt-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                <AlertCircle size={17} className="mt-0.5 shrink-0" />
                <div>{invoiceError}</div>
              </div>
            )}

            {/* Scrollable invoice table */}
            <div
              className="mt-5 overflow-x-auto overscroll-x-contain rounded-lg"
              role="region"
              aria-label="Invoice results table. Scroll horizontally to see all columns."
              tabIndex={0}
            >
              <table className="w-full min-w-[780px] border-collapse text-left">
                <thead>
                  <tr className="border-y border-slate-100 bg-slate-50 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                    <th className="px-4 py-3">Invoice</th>
                    <th className="px-4 py-3">Supplier</th>
                    <th className="px-4 py-3">Invoice date</th>
                    <th className="px-4 py-3">Due date</th>
                    <th className="px-4 py-3 text-right">Amount</th>
                    <th className="px-4 py-3">Status</th>
                  </tr>
                </thead>

                <tbody>
                  {invoiceLoading ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-12 text-center">
                        <div className="flex items-center justify-center gap-2 text-sm text-slate-400">
                          <LoaderCircle
                            className="animate-spin"
                            size={18}
                          />
                          Loading invoices...
                        </div>
                      </td>
                    </tr>
                  ) : invoiceError ? (
                    <tr>
                      <td
                        colSpan={6}
                        className="px-4 py-12 text-center text-sm text-slate-400"
                      >
                        Invoice data could not be loaded.
                      </td>
                    </tr>
                  ) : invoices.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-4 py-12 text-center">
                        <div className="flex flex-col items-center gap-2 text-slate-400">
                          <Search size={22} />

                          <p className="text-sm font-medium text-slate-600">
                            No invoices found
                          </p>

                          <p className="text-xs">
                            Try changing your search or filters.
                          </p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    invoices.map((invoice) => (
                      <tr
                        key={invoice.invoice_id}
                        className="border-b border-slate-100 text-xs transition hover:bg-slate-50"
                      >
                        <td className="px-4 py-4">
                          <button
                            type="button"
                            onClick={() => setSelectedInvoice(invoice)}
                            aria-haspopup="dialog"
                            aria-label={`View invoice ${invoice.invoice_id} details`}
                            className="font-semibold text-blue-700 underline-offset-2 transition hover:text-blue-900 hover:underline focus-visible:rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                          >
                            {invoice.invoice_id}
                          </button>
                        </td>

                        <td className="px-4 py-4">
                          <p className="font-medium text-slate-800">
                            {invoice.supplier}
                          </p>

                          <p className="mt-1 text-[10px] text-slate-400">
                            {invoice.country || '—'}
                            {invoice.category
                              ? ` · ${invoice.category}`
                              : ''}
                          </p>
                        </td>

                        <td className="px-4 py-4 text-slate-500">
                          {formatDate(invoice.invoice_date)}
                        </td>

                        <td className="px-4 py-4">
                          <span
                            className={
                              invoice.is_overdue
                                ? 'font-medium text-red-600'
                                : 'text-slate-500'
                            }
                          >
                            {formatDate(invoice.due_date)}
                          </span>
                        </td>

                        <td className="px-4 py-4 text-right font-semibold tabular-nums text-slate-800">
                          {currency(invoice.amount_eur)}
                        </td>

                        <td className="px-4 py-4">
                          {invoice.is_overdue ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-1 text-[10px] font-medium text-red-700">
                              <AlertCircle size={12} />
                              Overdue
                            </span>
                          ) : invoice.status.toLowerCase() === 'paid' ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-medium text-emerald-700">
                              <CheckCircle2 size={12} />
                              Paid
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-[10px] font-medium text-amber-700">
                              <AlertCircle size={12} />
                              Unpaid
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="mt-4 flex flex-col justify-between gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center">
              <p className="text-xs text-slate-500">
                {pagination.total_records === 0
                  ? 'No records'
                  : `Showing ${(page - 1) * pageSize + 1}–${Math.min(
                      page * pageSize,
                      pagination.total_records,
                    )} of ${pagination.total_records} invoices`}
              </p>

              <div className="flex w-full items-center justify-between gap-2 sm:w-auto sm:justify-start">
                <button
                  type="button"
                  onClick={() => setPage((current) => Math.max(1, current - 1))}
                  disabled={page <= 1 || invoiceLoading}
                  className="flex min-h-10 items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <ChevronLeft size={14} />
                  Previous
                </button>

                <span className="px-1 text-xs tabular-nums text-slate-500 sm:px-2">
                  Page {pagination.total_pages === 0 ? 0 : page} of{' '}
                  {pagination.total_pages}
                </span>

                <button
                  type="button"
                  onClick={() =>
                    setPage((current) =>
                      Math.min(pagination.total_pages, current + 1),
                    )
                  }
                  disabled={
                    page >= pagination.total_pages || invoiceLoading
                  }
                  className="flex min-h-10 items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Next
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </section>

          {/* Payment risk and POKO */}
          <section className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
            <article className="min-w-0 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="font-semibold text-slate-900">
                    Payment risk overview
                  </h3>

                  <p className="mt-1 text-xs text-slate-400">
                    Current overdue and not-yet-due exposure
                  </p>
                </div>

                <ShieldCheck className="shrink-0 text-slate-400" size={19} />
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <div className="min-w-0 rounded-xl bg-red-50 p-3 sm:p-4">
                  <div className="flex items-center gap-2 text-xs font-medium text-red-600">
                    <ArrowDownRight size={15} />
                    Overdue invoices
                  </div>

                  <p className="mt-3 text-xl font-semibold text-red-700">
                    {portfolio ? portfolio.overdue_invoice_count : '—'}
                  </p>

                  <p className="mt-1 text-xs text-red-500">
                    {portfolio ? currency(portfolio.overdue) : '—'}
                  </p>
                </div>

                <div className="min-w-0 rounded-xl bg-emerald-50 p-3 sm:p-4">
                  <div className="flex items-center gap-2 text-xs font-medium text-emerald-700">
                    <CheckCircle2 size={15} />
                    Not yet due
                  </div>

                  <p className="mt-3 text-xl font-semibold text-emerald-800">
                    {portfolio ? portfolio.not_due_invoice_count : '—'}
                  </p>

                  <p className="mt-1 text-xs text-emerald-600">
                    {portfolio ? currency(portfolio.not_due) : '—'}
                  </p>
                </div>
              </div>

              <div className="mt-5 flex items-start gap-2 rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs text-slate-500">
                <Activity className="mt-0.5 shrink-0" size={15} />
                Risk indicators are calculated by the financial backend.
              </div>
            </article>

            {/* POKO assistant */}
            <article
              id="ai-assistant"
              className="flex min-h-[360px] min-w-0 scroll-mt-6 flex-col rounded-xl border border-slate-200 bg-white shadow-sm sm:min-h-[400px]"
            >
              <div className="flex items-center gap-3 border-b border-slate-100 p-4 sm:p-5">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                  <BrainCircuit size={20} />
                </div>

                <div className="min-w-0">
                  <h3 className="font-semibold text-slate-900">
                    POKO
                  </h3>

                  <p className="text-[10px] text-slate-400">
                    Your Financial Operations Companion
                  </p>
                </div>

                <Sparkles className="ml-auto shrink-0 text-blue-500" size={17} />
              </div>

              <div className="max-h-[420px] min-h-[180px] flex-1 space-y-3 overflow-y-auto p-4">
                {messages.map((message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className={`max-w-[95%] break-words rounded-xl p-3 text-xs leading-5 ${
                      message.role === 'user'
                        ? 'ml-auto bg-[#172b4d] text-white'
                        : 'bg-slate-100 text-slate-700'
                    }`}
                  >
                    {message.content}
                  </div>
                ))}

                {asking && (
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <LoaderCircle className="animate-spin" size={14} />
                    Analysing your question...
                  </div>
                )}
              </div>

              <form
                onSubmit={askAssistant}
                className="flex items-center gap-2 border-t border-slate-100 p-3"
              >
                <input
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder="Ask about your invoices..."
                  aria-label="Ask POKO a question"
                  maxLength={1000}
                  className="min-h-11 min-w-0 flex-1 rounded-lg bg-slate-100 px-3 py-3 text-xs outline-none transition focus:ring-2 focus:ring-blue-200"
                />

                <button
                  type="submit"
                  disabled={!question.trim() || asking}
                  aria-label="Send question"
                  className="flex min-h-11 min-w-11 shrink-0 items-center justify-center rounded-lg bg-blue-600 p-3 text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <Send size={15} />
                </button>
              </form>
            </article>
          </section>

          {/* Footer */}
          <footer className="flex flex-col justify-between gap-2 border-t border-slate-200 py-4 text-[10px] text-slate-400 sm:flex-row">
            <span>Mittelstand AI · Financial Intelligence Platform</span>
            <span>React · TypeScript · FastAPI · PostgreSQL</span>
          </footer>
        </div>
      </main>

      {/* Invoice detail modal */}
      {selectedInvoice && (
        <InvoiceDetailPanel
          invoice={selectedInvoice}
          onClose={() => setSelectedInvoice(null)}
          currency={currency}
          formatDate={formatDate}
        />
      )}
    </div>
  )
}

export default App
