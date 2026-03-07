import { AnimatePresence, motion, useReducedMotion, useScroll, useSpring, useTransform } from 'framer-motion'
import {
  ArrowRight,
  BadgeCheck,
  BellRing,
  Bot,
  BrainCircuit,
  Building2,
  ChevronDown,
  ChevronRight,
  CreditCard,
  Download,
  Fuel,
  Home,
  Landmark,
  Mail,
  Menu,
  Phone,
  Play,
  Receipt,
  Send,
  Settings,
  ShieldCheck,
  ShoppingCart,
  Sparkles,
  Star,
  Target,
  Tv,
  UtensilsCrossed,
  Wallet,
  X,
  type LucideIcon,
} from 'lucide-react'
import { type ReactNode, useRef, useState } from 'react'
import './App.css'

type Tx = {
  icon: LucideIcon
  merchant: string
  date: string
  category: string
  amount: string
  color: string
  bg: string
}

type Feature = {
  id: string
  badge: string
  title: string
  description: string
  bullets: string[]
  cta: string
  theme: 'blue' | 'green' | 'pink'
  reversed?: boolean
  visual: 'expense' | 'accounts' | 'budget'
}

type PricingPlan = {
  name: string
  price: string
  subtitle: string
  highlight?: boolean
  features: string[]
  cta: string
}

const logos = ['Nexcore', 'TechFusion', 'datatech', 'Xconnect', 'vyrtua', 'bluebyte']

const statCards = [
  {
    value: '80%',
    label: 'of users save more each month',
    body: 'AI-driven budgeting insights surface waste and redirect spending toward goals automatically.',
    tone: 'blue',
  },
  {
    value: '$1.6M+',
    label: 'saved in goals',
    body: 'Users collectively funded vacations, emergency reserves, and long-term plans faster with automation.',
    tone: 'green',
  },
  {
    value: '95%',
    label: 'report less financial stress',
    body: 'Real-time tracking and personalized alerts increase clarity and reduce anxiety about monthly cash flow.',
    tone: 'orange',
  },
  {
    value: '2.8M+',
    label: 'transactions tracked',
    body: 'Connected accounts sync in one dashboard with categorization and actionable spending summaries.',
    tone: 'purple',
  },
] as const

const transactions: Tx[] = [
  {
    icon: ShoppingCart,
    merchant: 'Walmart',
    date: 'Sept 22, 2024',
    category: 'Groceries',
    amount: '-$45.30',
    color: 'var(--blue)',
    bg: 'rgba(41, 127, 255, 0.12)',
  },
  {
    icon: Sparkles,
    merchant: 'Utility Co.',
    date: 'Sept 21, 2024',
    category: 'Utilities',
    amount: '-$90.00',
    color: 'var(--green)',
    bg: 'rgba(64, 183, 94, 0.14)',
  },
  {
    icon: Tv,
    merchant: 'Netflix',
    date: 'Sept 20, 2024',
    category: 'Entertainment',
    amount: '-$15.99',
    color: 'var(--pink)',
    bg: 'rgba(184, 94, 214, 0.13)',
  },
  {
    icon: Fuel,
    merchant: 'Shell Gas',
    date: 'Sept 19, 2024',
    category: 'Transportation',
    amount: '-$65.20',
    color: 'var(--slate)',
    bg: 'rgba(90, 99, 112, 0.12)',
  },
  {
    icon: UtensilsCrossed,
    merchant: 'Chipotle',
    date: 'Sept 18, 2024',
    category: 'Dining',
    amount: '-$23.50',
    color: 'var(--orange)',
    bg: 'rgba(245, 159, 40, 0.15)',
  },
  {
    icon: Building2,
    merchant: 'Chase Bank',
    date: 'Sept 15, 2024',
    category: 'Income',
    amount: '+$2,500.00',
    color: 'var(--green)',
    bg: 'rgba(64, 183, 94, 0.14)',
  },
] as const

const features: Feature[] = [
  {
    id: 'expense-tracking',
    badge: 'Financial Management',
    title: 'Expense Tracking',
    description:
      'Automatically track, categorize, and analyze all your expenses in real time, across every connected account.',
    bullets: [
      'Real-time updates',
      'Automatic categorization',
      'Unified account view',
      'Detailed spending insights',
    ],
    cta: 'Read More About This',
    theme: 'blue',
    visual: 'expense',
  },
  {
    id: 'multi-account',
    badge: 'Financial Management',
    title: 'Multi-Account Sync',
    description:
      'Effortlessly link bank accounts, cards, and payment platforms into one dashboard for a unified financial overview.',
    bullets: [
      'All accounts in one place',
      'Real-time synchronization',
      'Financial management',
      'Financial overview',
    ],
    cta: 'Read More About This',
    theme: 'green',
    reversed: true,
    visual: 'accounts',
  },
  {
    id: 'custom-budgets',
    badge: 'Financial Management',
    title: 'Custom Budgets',
    description:
      'Create personalized budgets for categories like groceries, entertainment, and transport, then monitor usage against your limits.',
    bullets: [
      'Personalized spending limits',
      'Real-time budget tracking',
      'Flexible adjustments',
      'Visual spending alerts',
    ],
    cta: 'Read More About This',
    theme: 'pink',
    visual: 'budget',
  },
]

const pricingPlans: PricingPlan[] = [
  {
    name: 'Starter',
    price: '$0',
    subtitle: '/month · basic tracking',
    features: ['1 account connection', 'Expense tracking', 'Manual budgets', 'Email support'],
    cta: 'Get this Plan',
  },
  {
    name: 'Premium',
    price: '$20',
    subtitle: '/month · paid monthly',
    highlight: true,
    features: ['Unlimited accounts', 'AI insights', 'Savings automation', 'Priority support'],
    cta: 'Get this Plan',
  },
  {
    name: 'Business',
    price: '$49',
    subtitle: '/month · team workflows',
    features: ['Shared dashboards', 'Role access', 'Advanced exports', 'Onboarding support'],
    cta: 'Contact Us',
  },
]

const faqs = [
  {
    q: 'How do I link my bank accounts to Payble?',
    a: 'Use the secure connection flow to link banks, cards, and wallets. Connected accounts are synced into one dashboard and can be disconnected anytime.',
  },
  {
    q: 'Is Payble secure with financial information?',
    a: 'This demo simulates a production-grade experience with encrypted transfers, permissioned access, and read-only aggregation patterns for sensitive financial data.',
  },
  {
    q: 'Can I set multiple savings goals?',
    a: 'Yes. You can create parallel goals such as vacation, emergency fund, and gadgets, each with independent progress rules and automation triggers.',
  },
  {
    q: 'How do real-time budget alerts work?',
    a: 'Threshold monitors compare live spending against category budgets and surface proactive alerts before you cross configured limits.',
  },
  {
    q: 'Can I use Payble with multiple accounts and credit cards?',
    a: 'Yes. The multi-account sync experience is designed specifically for cards, banks, and payment platforms appearing in one unified view.',
  },
] as const

const revealVariants = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0 },
}

function Reveal({
  children,
  className,
  delay = 0,
}: {
  children: ReactNode
  className?: string
  delay?: number
}) {
  const reduceMotion = useReducedMotion()

  if (reduceMotion) {
    return <div className={className}>{children}</div>
  }

  return (
    <motion.div
      className={className}
      variants={revealVariants}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.55, ease: 'easeOut', delay }}
    >
      {children}
    </motion.div>
  )
}

function LogoMark() {
  return (
    <span className="logo-mark" aria-hidden="true">
      <span />
      <span />
      <span />
      <span />
      <i />
    </span>
  )
}

function SectionBadge({ children }: { children: ReactNode }) {
  return (
    <div className="section-badge">
      <span className="dot" />
      {children}
    </div>
  )
}

function DashboardDevice() {
  const reduceMotion = useReducedMotion()
  const stageRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({
    target: stageRef,
    offset: ['start 85%', 'end 20%'],
  })

  // Calibrated from Playwright probe of the real Framer page (`Ipad Content` matrix3d):
  // sin(theta) ~= 0.280927 at scrollY=0 => theta ~16.3deg, easing down to 0 by ~680px.
  const rotateXRaw = useTransform(scrollYProgress, [0, 0.55, 1], [16.3, 3, 0])
  const rotateZRaw = useTransform(scrollYProgress, [0, 1], [0, 0])
  const yRaw = useTransform(scrollYProgress, [0, 1], [140, 0])
  const scaleRaw = useTransform(scrollYProgress, [0, 1], [0.92, 1])

  const rotateX = useSpring(rotateXRaw, { stiffness: 120, damping: 24, mass: 0.4 })
  const rotateZ = useSpring(rotateZRaw, { stiffness: 120, damping: 24, mass: 0.4 })
  const y = useSpring(yRaw, { stiffness: 110, damping: 22, mass: 0.45 })
  const scale = useSpring(scaleRaw, { stiffness: 110, damping: 22, mass: 0.45 })

  return (
    <div ref={stageRef} className="device-tilt-stage">
      <motion.div
        className="device-wrap"
        style={
          reduceMotion
            ? undefined
            : {
                rotateX,
                rotateZ,
                y,
                scale,
                transformPerspective: 1800,
                transformOrigin: '50% 10%',
              }
        }
      >
        <motion.div
          className="device-shell"
          animate={
            reduceMotion
              ? undefined
              : {
                  y: [0, -6, 0],
                  rotate: [0, -0.2, 0],
                }
          }
          transition={
            reduceMotion
              ? undefined
              : {
                  duration: 8,
                  repeat: Number.POSITIVE_INFINITY,
                  ease: 'easeInOut',
                }
          }
        >
        <div className="device-camera" />
        <div className="device-screen">
          <aside className="dashboard-sidebar">
            <div className="brand-mini">
              <LogoMark />
            </div>
            <nav className="side-icons" aria-label="Dashboard navigation">
              <Home size={18} />
              <Receipt size={18} />
              <Target size={18} />
              <BellRing size={18} />
              <Settings size={18} />
            </nav>
            <div className="side-icons side-icons-bottom">
              <ShieldCheck size={18} />
              <Send size={18} />
            </div>
          </aside>

          <div className="dashboard-main">
            <div className="dashboard-topbar">
              <div>
                <p className="muted tiny">Good Morning!</p>
                <p className="dashboard-user">Cezara Dwayne</p>
              </div>
              <div className="topbar-actions">
                <button className="pill blue">
                  <Target size={14} />
                  Set Goal
                </button>
                <button className="icon-btn" aria-label="Notifications">
                  <BellRing size={14} />
                </button>
                <button className="icon-btn" aria-label="Profile">
                  <span className="avatar">CD</span>
                </button>
              </div>
            </div>

            <div className="mini-stats">
              <MetricCard title="Total Balance" value="$10,400" delta="+50%" deltaTone="up" accent="blue" />
              <MetricCard title="Income" value="$5,200" delta="+12%" deltaTone="up" accent="pink" />
              <MetricCard title="Expenses" value="$1,750" delta="-8%" deltaTone="down" accent="orange" />
            </div>

            <div className="dashboard-grid">
              <div className="panel large-panel">
                <div className="panel-head">
                  <h3>Recent Transactions</h3>
                  <span>⋮</span>
                </div>
                <div className="table-head">
                  <span>Merchant</span>
                  <span>Date</span>
                  <span>Category</span>
                  <span>Amount</span>
                </div>
                <div className="table-body">
                  {transactions.slice(0, 6).map((tx) => {
                    const Icon = tx.icon
                    return (
                      <div className="table-row" key={`${tx.merchant}-${tx.date}`}>
                        <div className="merchant-cell">
                          <span className="merchant-icon" style={{ background: tx.bg, color: tx.color }}>
                            <Icon size={13} />
                          </span>
                          <span>{tx.merchant}</span>
                        </div>
                        <span>{tx.date}</span>
                        <span>{tx.category}</span>
                        <span className={tx.amount.startsWith('+') ? 'amount-up' : 'amount-down'}>{tx.amount}</span>
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="dashboard-aside">
                <div className="saving-goal-card">
                  <div className="panel-head">
                    <h3>Recent Saving Goal</h3>
                    <span>⋮</span>
                  </div>
                  <div className="goal-ring">
                    <svg viewBox="0 0 120 120" aria-hidden="true">
                      <circle cx="60" cy="60" r="42" className="goal-track" />
                      <motion.circle
                        cx="60"
                        cy="60"
                        r="42"
                        className="goal-progress"
                        initial={{ pathLength: 0 }}
                        whileInView={{ pathLength: 0.75 }}
                        viewport={{ once: true }}
                        transition={{ duration: 1.1, ease: 'easeOut' }}
                        pathLength={0.75}
                      />
                    </svg>
                    <span>75%</span>
                  </div>
                  <div className="goal-meta">
                    <div>
                      <p className="muted tiny">Vacation Fund</p>
                      <p>$3,000 / $4,000</p>
                    </div>
                    <div className="goal-date">Dec, 01 2024</div>
                  </div>
                </div>

                <div className="panel cards-panel">
                  <div className="panel-head">
                    <h3>My Cards</h3>
                    <span>⋮</span>
                  </div>
                  <div className="cards-stack">
                    <div className="bank-card layer-1" />
                    <div className="bank-card layer-2" />
                    <div className="bank-card main">
                      <div>
                        <p className="tiny card-label">Debit Card</p>
                        <p className="card-number">•••• •••• •••• 4456</p>
                      </div>
                      <div className="card-footer">
                        <span>Cezara Dwayne</span>
                        <span>02/27</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

function MetricCard({
  title,
  value,
  delta,
  deltaTone,
  accent,
}: {
  title: string
  value: string
  delta: string
  deltaTone: 'up' | 'down'
  accent: 'blue' | 'pink' | 'orange'
}) {
  return (
    <div className={`metric-card accent-${accent}`}>
      <div className="metric-title">{title}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-meta">
        <span className="muted tiny">From last month</span>
        <span className={deltaTone === 'up' ? 'amount-up' : 'amount-down'}>{delta}</span>
      </div>
    </div>
  )
}

function MarqueeLogos() {
  const items = [...logos, ...logos]

  return (
    <div className="logo-marquee" aria-label="Integrations logos">
      <motion.div
        className="logo-marquee-track"
        animate={{ x: ['0%', '-50%'] }}
        transition={{
          duration: 22,
          repeat: Number.POSITIVE_INFINITY,
          ease: 'linear',
        }}
      >
        {items.map((logo, idx) => (
          <div className="logo-pill" key={`${logo}-${idx}`}>
            <span className="logo-pill-icon" />
            <span>{logo}</span>
          </div>
        ))}
      </motion.div>
    </div>
  )
}

function ThreeColumnFlow() {
  const columns = [
    {
      title: 'Problems',
      tone: 'red',
      items: [
        'Struggling to track all your expenses in one place?',
        'Overspending without realizing it?',
        'Difficult to save for long-term goals?',
      ],
    },
    {
      title: 'Handle',
      tone: 'blue',
      items: [
        'Managing multiple accounts can feel overwhelming.',
        "Without real-time updates, it's easy to lose track of spending.",
        'Saving for long-term goals requires consistency and planning.',
      ],
    },
    {
      title: 'Solutions',
      tone: 'green',
      items: [
        'Payble integrates your accounts into one dashboard.',
        "Receive real-time alerts when you're approaching budget limits.",
        'Set custom savings goals and let AI automate the path to reaching them.',
      ],
    },
  ] as const

  return (
    <div className="flow-grid">
      {columns.map((column, i) => (
        <div className="flow-card" key={column.title}>
          <div className="flow-title-row">
            <h3>{column.title}</h3>
            {i < columns.length - 1 ? (
              <span className="flow-arrow" aria-hidden="true">
                <ArrowRight size={16} />
              </span>
            ) : null}
          </div>
          <ul>
            {column.items.map((item) => (
              <li key={item} className={`dot-${column.tone}`}>
                {item}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

function FeatureVisual({ visual }: { visual: Feature['visual'] }) {
  if (visual === 'accounts') {
    return (
      <div className="visual-stage visual-green">
        <motion.div className="floating-card left-card" whileInView={{ y: [8, 0] }} transition={{ duration: 0.6 }} viewport={{ once: true }}>
          <div className="panel-head small">
            <h4>Credit Cards</h4>
            <span>⋮</span>
          </div>
          <div className="simple-list">
            <div><CreditCard size={14} /> Chase Bank <b>-$80</b></div>
            <div><CreditCard size={14} /> Venture Capital <b>-$30</b></div>
          </div>
          <div className="panel-head small pad-top">
            <h4>Payment Platforms</h4>
          </div>
          <div className="simple-list">
            <div><Wallet size={14} /> Spendly <b>$1,000</b></div>
            <div><Wallet size={14} /> Reify <b>$2,000</b></div>
          </div>
        </motion.div>

        <motion.div className="floating-card right-card" whileInView={{ y: [14, 0] }} transition={{ duration: 0.7, delay: 0.1 }} viewport={{ once: true }}>
          <div className="panel-head small">
            <h4>Bank Accounts</h4>
            <span>⋮</span>
          </div>
          <div className="simple-list compact">
            <div><Landmark size={14} /> Chase Bank <b>$6,500.00</b></div>
            <div><Landmark size={14} /> Venture Capital <b>$2,000.00</b></div>
          </div>
        </motion.div>
      </div>
    )
  }

  if (visual === 'budget') {
    return (
      <div className="visual-stage visual-pink">
        <div className="budget-float-top">
          <div>
            <span className="muted tiny">Total Budget</span>
            <b>$1,150.00</b>
          </div>
          <div>
            <span className="muted tiny">Total Spent</span>
            <b>$955.00</b>
          </div>
        </div>
        <div className="budget-panel">
          <div className="panel-head small">
            <h4>Budget Category Breakdown</h4>
            <span>⋮</span>
          </div>
          {[
            ['Groceries', '$500', '$375', 75, 'var(--green)'],
            ['Entertainment', '$200', '$120', 60, 'var(--blue)'],
            ['Transportation', '$150', '$140', 93, 'var(--orange)'],
            ['Dining', '$300', '$320', 107, 'var(--red)'],
          ].map(([label, budget, spent, progress, color]) => (
            <div className="budget-row" key={String(label)}>
              <span>{label}</span>
              <span>{budget}</span>
              <span>{spent}</span>
              <div className="progress-inline">
                <div className="progress-track-inline">
                  <motion.div
                    className="progress-bar-inline"
                    style={{ background: color as string }}
                    initial={{ width: 0 }}
                    whileInView={{ width: `${progress}%` }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.8 }}
                  />
                </div>
                <span>{progress}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="visual-stage visual-blue">
      <div className="expense-panel">
        <div className="panel-head small">
          <h4>Recent Expenses</h4>
          <span>⋮</span>
        </div>
        <div className="expense-mini-head">
          <span>Merchant</span>
          <span>Date</span>
          <span>Category</span>
          <span>Amount</span>
        </div>
        {transactions.slice(0, 5).map((tx) => {
          const Icon = tx.icon
          return (
            <div className="expense-mini-row" key={`${tx.merchant}-feature`}>
              <span className="merchant-cell">
                <span className="merchant-icon" style={{ background: tx.bg, color: tx.color }}>
                  <Icon size={12} />
                </span>
                {tx.merchant}
              </span>
              <span>{tx.date}</span>
              <span>{tx.category}</span>
              <span>{tx.amount}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function FeatureBlock({ feature }: { feature: Feature }) {
  return (
    <Reveal className="feature-block">
      <div className={`feature-grid ${feature.reversed ? 'reversed' : ''}`}>
        <div className="feature-copy">
          <SectionBadge>{feature.badge}</SectionBadge>
          <h2>{feature.title}</h2>
          <p>{feature.description}</p>
          <div className="bullet-grid">
            {feature.bullets.map((bullet) => (
              <div className="bullet-pill" key={bullet}>
                <BadgeCheck size={14} />
                <span>{bullet}</span>
              </div>
            ))}
          </div>
          <button className="btn btn-dark">{feature.cta}</button>
        </div>
        <FeatureVisual visual={feature.visual} />
      </div>
    </Reveal>
  )
}

function SavingsBento() {
  return (
    <div className="savings-grid">
      <Reveal className="savings-card tall" delay={0.05}>
        <div className="panel-head small">
          <h4>Savings Goals</h4>
          <span>⋮</span>
        </div>
        <div className="goal-list">
          <div className="goal-item">
            <div>
              <strong>Vacation</strong>
              <p className="muted tiny">$3,000 of $4,000</p>
            </div>
            <span>75%</span>
          </div>
          <div className="goal-progress-row">
            <motion.div className="goal-fill blue" initial={{ width: 0 }} whileInView={{ width: '75%' }} viewport={{ once: true }} transition={{ duration: 0.9 }} />
          </div>
          <div className="goal-item">
            <div>
              <strong>Emergency</strong>
              <p className="muted tiny">$5,800 of $10,000</p>
            </div>
            <span>58%</span>
          </div>
          <div className="goal-progress-row">
            <motion.div className="goal-fill green" initial={{ width: 0 }} whileInView={{ width: '58%' }} viewport={{ once: true }} transition={{ duration: 0.9, delay: 0.1 }} />
          </div>
        </div>
      </Reveal>

      <Reveal className="savings-card" delay={0.1}>
        <div className="panel-head small">
          <h4>AI Insights</h4>
          <span>⋮</span>
        </div>
        <div className="insight-stack">
          <div className="insight-row">
            <BrainCircuit size={16} />
            <span>Reduce dining spend by 12% to hit your vacation goal 10 days earlier.</span>
          </div>
          <div className="insight-row">
            <Bot size={16} />
            <span>Round-up transfers can save an extra $180/month based on recent behavior.</span>
          </div>
        </div>
      </Reveal>

      <Reveal className="savings-card" delay={0.15}>
        <div className="panel-head small">
          <h4>Round-Up Savings</h4>
          <span>⋮</span>
        </div>
        <div className="chip-cloud">
          <span className="chip"><ShoppingCart size={14} /> Groceries +$3.20</span>
          <span className="chip"><UtensilsCrossed size={14} /> Coffee +$0.60</span>
          <span className="chip"><Fuel size={14} /> Gas +$1.15</span>
          <span className="chip"><Tv size={14} /> Subscriptions +$0.85</span>
        </div>
      </Reveal>

      <Reveal className="savings-card wide" delay={0.2}>
        <div className="panel-head small">
          <h4>Automated Savings Transfers</h4>
          <span>⋮</span>
        </div>
        <div className="transfer-timeline">
          <div className="timeline-row">
            <span className="timeline-dot green" />
            <div>
              <strong>Salary Rule Triggered</strong>
              <p className="muted tiny">Move 12% of income to Emergency Fund on payday.</p>
            </div>
            <b>$624.00</b>
          </div>
          <div className="timeline-row">
            <span className="timeline-dot blue" />
            <div>
              <strong>Weekly Auto Save</strong>
              <p className="muted tiny">Schedule recurring transfers every Friday.</p>
            </div>
            <b>$80.00</b>
          </div>
        </div>
      </Reveal>
    </div>
  )
}

function PricingSection() {
  return (
    <div className="pricing-grid">
      {pricingPlans.map((plan, idx) => (
        <Reveal className={`pricing-card ${plan.highlight ? 'highlight' : ''}`} key={plan.name} delay={idx * 0.06}>
          {plan.highlight ? <div className="pricing-pill">PREMIUM</div> : null}
          <div className="pricing-head">
            <h3>{plan.name}</h3>
            <div className="pricing-price">{plan.price}</div>
            <p>{plan.subtitle}</p>
          </div>
          <ul className="pricing-features">
            {plan.features.map((feature) => (
              <li key={feature}>
                <BadgeCheck size={14} /> {feature}
              </li>
            ))}
          </ul>
          <button className={`btn ${plan.highlight ? 'btn-dark' : 'btn-outline'}`}>{plan.cta}</button>
        </Reveal>
      ))}
    </div>
  )
}

function TestimonialsSection() {
  const cards = [
    {
      name: 'Maya Peterson',
      role: 'Freelancer',
      text: 'Payble turned scattered account tracking into one routine. The savings automation is the first workflow I actually stick with.',
    },
    {
      name: 'Leon Grant',
      role: 'Founder',
      text: 'The budget alerts and transaction visibility reduced overspending across both my personal and business cards.',
    },
    {
      name: 'Sofia Chen',
      role: 'Product Designer',
      text: 'The UI makes dense financial data feel calm. I can spot problem categories in seconds and adjust the plan fast.',
    },
  ] as const

  return (
    <div className="testimonials-grid">
      {cards.map((card, idx) => (
        <Reveal className="testimonial-card" key={card.name} delay={idx * 0.05}>
          <div className="stars" aria-hidden="true">
            {Array.from({ length: 5 }).map((_, i) => (
              <Star key={i} size={14} fill="currentColor" />
            ))}
          </div>
          <p>{card.text}</p>
          <div className="testimonial-meta">
            <div className="avatar">{card.name.split(' ').map((n) => n[0]).join('')}</div>
            <div>
              <strong>{card.name}</strong>
              <span>{card.role}</span>
            </div>
          </div>
        </Reveal>
      ))}
    </div>
  )
}

function FAQSection() {
  const [open, setOpen] = useState<number>(0)

  return (
    <div className="faq-list">
      {faqs.map((faq, idx) => {
        const isOpen = open === idx
        return (
          <div className={`faq-item ${isOpen ? 'open' : ''}`} key={faq.q}>
            <button className="faq-trigger" onClick={() => setOpen(isOpen ? -1 : idx)}>
              <span>{faq.q}</span>
              <motion.span animate={{ rotate: isOpen ? 180 : 0 }} transition={{ duration: 0.2 }}>
                <ChevronDown size={18} />
              </motion.span>
            </button>
            <AnimatePresence initial={false}>
              {isOpen ? (
                <motion.div
                  className="faq-content"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.24, ease: 'easeOut' }}
                >
                  <p>{faq.a}</p>
                </motion.div>
              ) : null}
            </AnimatePresence>
          </div>
        )
      })}
    </div>
  )
}

function FloatingWidget() {
  const [closed, setClosed] = useState(false)

  if (closed) {
    return (
      <button className="widget-reopen" onClick={() => setClosed(false)}>
        Open demo widget
      </button>
    )
  }

  return (
    <div className="floating-widget" role="complementary" aria-label="Template actions">
      <button className="widget-close" onClick={() => setClosed(true)} aria-label="Close widget">
        <X size={14} />
      </button>
      <div className="widget-preview">
        <div className="widget-thumb" />
        <div className="widget-copy">
          <strong>Template Demo</strong>
          <span>Preview actions</span>
        </div>
      </div>
      <button className="widget-action primary">New Template</button>
      <button className="widget-action dark">Free Remix</button>
      <button className="widget-action light">Made with Framer-style UI</button>
    </div>
  )
}

function App() {
  const [menuOpen, setMenuOpen] = useState(false)
  const navLinks = ['Home', 'Features', 'Pricing', 'Blog', 'Contact']

  return (
    <div className="app-shell">
      <div className="bg-glow glow-a" />
      <div className="bg-glow glow-b" />

      <header className="site-header">
        <div className="header-inner">
          <a href="#top" className="brand">
            <LogoMark />
            <span>Payble</span>
          </a>

          <nav className="desktop-nav" aria-label="Primary">
            {navLinks.map((link) => (
              <a key={link} href={`#${link.toLowerCase()}`}>
                {link}
              </a>
            ))}
          </nav>

          <div className="header-actions">
            <button className="btn btn-dark header-cta">FREE Remix</button>
            <button className="menu-toggle" onClick={() => setMenuOpen((v) => !v)} aria-label="Toggle menu">
              {menuOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
          </div>
        </div>

        <AnimatePresence>
          {menuOpen ? (
            <motion.div
              className="mobile-menu"
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
            >
              {navLinks.map((link) => (
                <a key={link} href={`#${link.toLowerCase()}`} onClick={() => setMenuOpen(false)}>
                  {link}
                </a>
              ))}
              <button className="btn btn-dark">FREE Remix</button>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </header>

      <main id="top">
        <section className="hero dots-bg">
          <Reveal className="hero-copy">
            <SectionBadge>Smart AI for Your Finances</SectionBadge>
            <h1>Your AI-Powered Financial Assistant</h1>
            <p>
              From detailed budgeting to custom savings goals, this Payble-inspired simulation automates the visual flow of modern personal finance experiences.
            </p>
            <div className="hero-actions">
              <button className="btn btn-dark btn-lg">Start Saving Now</button>
              <button className="btn btn-ghost btn-lg">
                <Play size={14} fill="currentColor" /> Presentation
              </button>
            </div>
          </Reveal>

          <Reveal className="hero-device" delay={0.08}>
            <DashboardDevice />
          </Reveal>
        </section>

        <section className="logos-section" id="features">
          <MarqueeLogos />
        </section>

        <section className="content-section centered-block">
          <Reveal className="section-head">
            <SectionBadge>Impressive Stats</SectionBadge>
            <h2>Our Results in Numbers</h2>
            <p>
              Discover the real impact a finance automation platform can make on budgeting, saving, and long-term financial confidence.
            </p>
          </Reveal>
          <div className="stats-grid">
            {statCards.map((card, idx) => (
              <Reveal className={`stat-card tone-${card.tone}`} key={card.value} delay={idx * 0.05}>
                <div className="stat-value">{card.value}</div>
                <div className="stat-label">{card.label}</div>
                <p>{card.body}</p>
              </Reveal>
            ))}
          </div>
        </section>

        <section className="content-section centered-block soft-section">
          <Reveal className="section-head">
            <SectionBadge>Financial Roadblocks</SectionBadge>
            <h2>Struggle Financial Situations?</h2>
            <p>
              A structured product experience can translate scattered pain points into clear actions, alerts, and automation rules.
            </p>
          </Reveal>
          <Reveal delay={0.08}>
            <ThreeColumnFlow />
          </Reveal>
        </section>

        <section className="features-stack">
          {features.map((feature) => (
            <section className="content-section feature-section" id={feature.id} key={feature.id}>
              <FeatureBlock feature={feature} />
            </section>
          ))}
        </section>

        <section className="content-section centered-block" id="pricing">
          <Reveal className="section-head">
            <SectionBadge>Smart Savings</SectionBadge>
            <h2>Optimize Your Savings Journey</h2>
            <p>
              Whether it’s a vacation or an emergency fund, modular components and automation patterns help users reach goals faster.
            </p>
          </Reveal>
          <SavingsBento />
        </section>

        <section className="content-section centered-block soft-section">
          <Reveal className="section-head">
            <SectionBadge>Impact Stories</SectionBadge>
            <h2>How This Experience Changes Lives</h2>
            <p>
              High-trust financial UX depends on clear hierarchy, calm visuals, and fast comprehension of what matters now.
            </p>
          </Reveal>
          <TestimonialsSection />
        </section>

        <section className="content-section centered-block" id="blog">
          <Reveal className="section-head">
            <SectionBadge>Flexible Pricing</SectionBadge>
            <h2>Flexible Pricing for Every Lifestyle</h2>
            <p>
              A Payble-style pricing module with strong hierarchy, highlighted plan emphasis, and compact feature comparison.
            </p>
          </Reveal>
          <PricingSection />
        </section>

        <section className="content-section centered-block soft-section" id="contact">
          <Reveal className="section-head">
            <SectionBadge>Common Questions & Answers</SectionBadge>
            <h2>FAQ</h2>
            <p>
              The accordion interaction is included so the prototype can be reused as a UX benchmark component inside another repo.
            </p>
          </Reveal>
          <Reveal delay={0.05}>
            <FAQSection />
          </Reveal>
        </section>

        <section className="content-section centered-block app-cta-section">
          <Reveal className="app-cta">
            <div>
              <SectionBadge>Download Mobile App</SectionBadge>
              <h2>Your Guide to Smarter Money Management</h2>
              <p>Use this as a reusable hero/CTA module when migrating the prototype to a new repository.</p>
            </div>
            <div className="app-cta-actions">
              <button className="btn btn-dark btn-lg"><Download size={15} /> App Store</button>
              <button className="btn btn-outline btn-lg"><ChevronRight size={15} /> Google Play</button>
            </div>
          </Reveal>
        </section>
      </main>

      <footer className="site-footer">
        <div className="footer-top">
          <a href="#top" className="brand footer-brand">
            <LogoMark />
            <span>Payble</span>
          </a>
          <div className="footer-newsletter">
            <h3>Subscribe to Newsletter</h3>
            <label className="newsletter-input">
              <Mail size={16} />
              <input type="email" placeholder="email@payble.com" />
              <button aria-label="Subscribe">Subscribe</button>
            </label>
          </div>
        </div>
        <div className="footer-links">
          <a href="mailto:email@payble.com"><Mail size={14} /> email@payble.com</a>
          <a href="tel:+44111333555"><Phone size={14} /> +44 111 333 555</a>
          <a href="#">Privacy Policy</a>
          <a href="#">Cookie Policy</a>
          <a href="#">Terms of Service</a>
          <a href="#">Refund Policy</a>
        </div>
      </footer>

      <FloatingWidget />
    </div>
  )
}

export default App
