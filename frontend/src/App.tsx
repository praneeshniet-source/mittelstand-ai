
import { useEffect, useState, type FormEvent } from 'react'
import {
  Activity,
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  Bot,
  BrainCircuit,
  Building2,
  CheckCircle2,
  ChevronDown,
  CircleHelp,
  FileText,
  LayoutDashboard,
  LoaderCircle,
  MessageSquare,
  Send,
  Settings,
  ShieldCheck,
  Sparkles,
  Wallet,
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

type AssistantMessage = {
  role: 'user' | 'assistant'
  content: string
}

const currency = (value: number) =>
  new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(value)

function App() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [loading, setLoading] = useState(true)
  const [apiError, setApiError] = useState('')
  const [apiConnected, setApiConnected] = useState(false)

  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<AssistantMessage[]>([
    {
      role: 'assistant',
      content:
        'Hello! I am your financial operations assistant. Ask me about overdue invoices, outstanding payments, or supplier exposure.',
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
          <nav className="space-y-1">
            <a className="flex items-center gap-3 rounded-lg bg-blue-500/15 px-3 py-3 text-sm font-medium text-blue-300">
              <LayoutDashboard size={18} />
              Overview
            </a>
            <a className="flex items-center gap-3 rounded-lg px-3 py-3 text-sm text-slate-400 transition hover:bg-white/5 hover:text-white">
              <FileText size={18} />
              Invoices
            </a>
            <a className="flex items-center gap-3 rounded-lg px-3 py-3 text-sm text-slate-400 transition hover:bg-white/5 hover:text-white">
              <Building2 size={18} />
              Suppliers
            </a>
            <a className="flex items-center gap-3 rounded-lg px-3 py-3 text-sm text-slate-400 transition hover:bg-white/5 hover:text-white">
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

      <main className="min-h-screen lg:ml-[250px]">
        <header className="flex h-[76px] items-center justify-between border-b border-slate-200 bg-white px-5 sm:px-8">
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
                {apiConnected ? 'Backend connected' : 'Backend unavailable'}
              </span>
            </div>
            <button
              aria-label="Help"
              className="hidden rounded-full border border-slate-200 p-2 text-slate-500 sm:block"
            >
              <CircleHelp size={17} />
            </button>
          </div>
        </header>

        <div className="mx-auto max-w-[1500px] space-y-6 p-5 sm:p-8">
          <section className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
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

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {metrics.map((metric) => {
              const Icon = metric.icon

              return (
                <article
                  key={metric.label}
                  className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-medium text-slate-500">
                      {metric.label}
                    </p>
                    <div className="rounded-lg bg-slate-100 p-2 text-slate-600">
                      <Icon size={17} />
                    </div>
                  </div>
                  <div className="mt-4 min-h-9 text-[25px] font-semibold tracking-tight text-slate-900">
                    {loading ? (
                      <LoaderCircle
                        className="animate-spin text-slate-400"
                        size={22}
                      />
                    ) : (
                      metric.value
                    )}
                  </div>
                  <p className="mt-2 text-[11px] text-slate-400">
                    {metric.description}
                  </p>
                </article>
              )
            })}
          </section>

          <section className="grid gap-5 xl:grid-cols-[1.6fr_1fr]">
            <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900">
                    Invoice portfolio
                  </h3>
                  <p className="mt-1 text-xs text-slate-400">
                    Financial distribution by payment status
                  </p>
                </div>
                <span className="rounded-lg bg-slate-100 px-3 py-2 text-[11px] text-slate-600">
                  EUR
                </span>
              </div>

              <div className="mt-6 h-[260px]">
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

            <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
              <h3 className="font-semibold text-slate-900">
                Payment composition
              </h3>
              <p className="mt-1 text-xs text-slate-400">
                Paid versus outstanding invoice value
              </p>

              <div className="relative mt-3 h-[205px]">
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
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-2 text-slate-500">
                    <span className="h-2.5 w-2.5 rounded-full bg-[#4778d9]" />
                    Paid
                  </span>
                  <strong className="text-slate-800">
                    {portfolio ? currency(portfolio.paid) : '—'}
                  </strong>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-2 text-slate-500">
                    <span className="h-2.5 w-2.5 rounded-full bg-[#f0a34a]" />
                    Outstanding
                  </span>
                  <strong className="text-slate-800">
                    {portfolio ? currency(portfolio.unpaid) : '—'}
                  </strong>
                </div>
              </div>
            </article>
          </section>

          <section className="grid gap-5 xl:grid-cols-[1.6fr_1fr]">
            <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-900">
                    Payment risk overview
                  </h3>
                  <p className="mt-1 text-xs text-slate-400">
                    Current overdue and not-yet-due exposure
                  </p>
                </div>
                <ShieldCheck className="text-slate-400" size={19} />
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-red-50 p-4">
                  <div className="flex items-center gap-2 text-xs font-medium text-red-600">
                    <ArrowDownRight size={15} />
                    Overdue invoices
                  </div>
                  <p className="mt-3 text-xl font-semibold text-red-700">
                    {portfolio
                      ? portfolio.overdue_invoice_count
                      : '—'}
                  </p>
                  <p className="mt-1 text-xs text-red-500">
                    {portfolio ? currency(portfolio.overdue) : '—'}
                  </p>
                </div>
                <div className="rounded-xl bg-emerald-50 p-4">
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

              <div className="mt-5 flex items-center gap-2 rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs text-slate-500">
                <Activity size={15} />
                Risk indicators are calculated by the financial backend.
              </div>
            </article>

            <article className="flex min-h-[300px] flex-col rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="flex items-center gap-3 border-b border-slate-100 p-5">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                  <Bot size={20} />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">
                    AI Finance Assistant
                  </h3>
                  <p className="text-[10px] text-slate-400">
                    Ask questions about your finances
                  </p>
                </div>
                <Sparkles className="ml-auto text-blue-500" size={17} />
              </div>

              <div className="flex-1 space-y-3 overflow-y-auto p-4">
                {messages.map((message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className={`max-w-[95%] rounded-xl p-3 text-xs leading-5 ${
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
                  maxLength={1000}
                  className="min-w-0 flex-1 rounded-lg bg-slate-100 px-3 py-3 text-xs outline-none transition focus:ring-2 focus:ring-blue-200"
                />
                <button
                  type="submit"
                  disabled={!question.trim() || asking}
                  aria-label="Send question"
                  className="rounded-lg bg-blue-600 p-3 text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <Send size={15} />
                </button>
              </form>
            </article>
          </section>

          <footer className="flex flex-col justify-between gap-2 border-t border-slate-200 py-4 text-[10px] text-slate-400 sm:flex-row">
            <span>Mittelstand AI · Financial Intelligence Platform</span>
            <span>React · TypeScript · FastAPI · PostgreSQL</span>
          </footer>
        </div>
      </main>
    </div>
  )
}

export default App
