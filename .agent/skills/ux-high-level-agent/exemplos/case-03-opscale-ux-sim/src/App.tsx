import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import {
  ArrowRight,
  BarChart3,
  Bot,
  CalendarRange,
  ChevronDown,
  CircleDollarSign,
  Cloud,
  Cpu,
  Database,
  Gauge,
  LineChart,
  Mail,
  Menu,
  Phone,
  Shield,
  Sparkles,
  Users,
  Workflow,
  X,
} from 'lucide-react'
import { type ReactNode, useState } from 'react'
import './App.css'

type FeatureCard = {
  title: string
  body: string
  icon: ReactNode
  tone: 'soft' | 'ink'
}

type PricingPlan = {
  name: string
  price: string
  period: string
  badge?: string
  featured?: boolean
  points: string[]
}

type FAQ = {
  q: string
  a: string
}

type TeamMember = {
  name: string
  role: string
  accent: string
}

const navItems = ['Features', 'Integrate', 'Services', 'Pricing', 'Reviews', 'FAQ']

const logos = ['Logoipsum', 'Goipsum', 'Logoipsum', '8 Logoipsum', 'Lgo', 'Logoflow']

const features: FeatureCard[] = [
  {
    title: 'AI-Powered Insights',
    body: 'Surface revenue opportunities and churn risks with live signals across your pipeline.',
    icon: <Bot size={18} />,
    tone: 'soft',
  },
  {
    title: 'Task Automation',
    body: 'Automate repetitive CRM and reporting steps with no-code workflows and alerts.',
    icon: <Workflow size={18} />,
    tone: 'soft',
  },
  {
    title: 'Predictive Sales Analytics',
    body: 'Forecast trends and compare targets versus actuals with explainable AI summaries.',
    icon: <LineChart size={18} />,
    tone: 'ink',
  },
  {
    title: 'Smart CRM Integration',
    body: 'Connect hub tools, sync leads, and unify your sales signals in one operational model.',
    icon: <Database size={18} />,
    tone: 'soft',
  },
  {
    title: 'Live Performance',
    body: 'Monitor account performance and campaign velocity with high-frequency dashboards.',
    icon: <Gauge size={18} />,
    tone: 'soft',
  },
  {
    title: 'Secure Cloud Storage',
    body: 'Protected data pipelines, access controls, and enterprise-grade infrastructure by default.',
    icon: <Cloud size={18} />,
    tone: 'ink',
  },
]

const plans: PricingPlan[] = [
  {
    name: 'Starter',
    price: '$19.99',
    period: '/month',
    points: ['AI dashboard', 'Basic automation', 'Email support', '5 team members'],
  },
  {
    name: 'Growth',
    price: '$49.99',
    period: '/month',
    featured: true,
    badge: 'Most Popular',
    points: ['Everything in Starter', 'Advanced automations', 'Sales forecasting', 'Priority support'],
  },
  {
    name: 'Custom',
    price: 'Custom',
    period: '',
    points: ['Enterprise security', 'Dedicated onboarding', 'Custom integrations', 'SLA & admin controls'],
  },
]

const faqs: FAQ[] = [
  {
    q: 'How fast can we launch Opscale?',
    a: 'Most teams ship their first dashboard and automation workflows in a few days, not weeks, with starter templates and guided setup.',
  },
  {
    q: 'Does Opscale connect to our CRM and analytics stack?',
    a: 'Yes. Opscale is designed for integration-first workflows and supports common CRM, BI and communication tools with sync orchestration.',
  },
  {
    q: 'Can we start with a small team and scale later?',
    a: 'Yes. Plans are designed to scale from startup teams to enterprise rollouts without rebuilding your workspace architecture.',
  },
  {
    q: 'Is there enterprise-grade security?',
    a: 'Role-based access, secure cloud storage, auditability and managed infrastructure are built into the product direction and enterprise setup.',
  },
]

const team: TeamMember[] = [
  { name: 'Nina Cole', role: 'AI Product Lead', accent: '#c9bcff' },
  { name: 'Marcus Lee', role: 'Revenue Ops', accent: '#d8ff8c' },
  { name: 'Sofia Kim', role: 'Data Strategist', accent: '#ffd9a8' },
  { name: 'Andre Hall', role: 'Solutions Architect', accent: '#bde8ff' },
]

const revealVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
}

function Reveal({ children, delay = 0, className }: { children: ReactNode; delay?: number; className?: string }) {
  const reduce = useReducedMotion()
  if (reduce) return <div className={className}>{children}</div>

  return (
    <motion.div
      className={className}
      variants={revealVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.15 }}
      transition={{ duration: 0.52, ease: 'easeOut', delay }}
    >
      {children}
    </motion.div>
  )
}

function Brand({ dark = false }: { dark?: boolean }) {
  return (
    <div className={`ops-brand ${dark ? 'dark' : ''}`} aria-label="Opscale">
      <span className="ops-brand-mark" aria-hidden="true">
        <i />
        <i />
        <i />
        <i />
      </span>
      <span>Opscale</span>
    </div>
  )
}

function TopHeader() {
  const [open, setOpen] = useState(false)

  return (
    <header className="top-header">
      <div className="top-header-shell">
        <Brand />

        <nav className="top-nav" aria-label="Primary">
          {navItems.map((item) => (
            <a href={`#${item.toLowerCase()}`} key={item}>
              {item}
            </a>
          ))}
        </nav>

        <button className="pill-btn dark desktop-only" type="button">
          Try Opscale
        </button>

        <button
          type="button"
          className="mobile-icon-btn"
          aria-label={open ? 'Close menu' : 'Open menu'}
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            className="mobile-menu-sheet"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
          >
            {navItems.map((item) => (
              <a href={`#${item.toLowerCase()}`} key={item} onClick={() => setOpen(false)}>
                {item}
              </a>
            ))}
            <button type="button" className="pill-btn dark">
              Try Opscale
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}

function DashboardMockup() {
  const bars = [35, 42, 54, 68, 44, 58, 73, 41, 52, 64, 39, 48]
  const progress = [92, 67, 54]

  return (
    <div className="dashboard-shell">
      <div className="dashboard-sidebar">
        <Brand />
        <ul>
          {['Overview', 'Analytics', 'AI Insights', 'Customers', 'Sales', 'Reports', 'Integrations', 'Settings', 'Support'].map((item, i) => (
            <li key={item} className={i === 1 ? 'active' : ''}>
              <span className="menu-dot" />
              {item}
            </li>
          ))}
        </ul>
      </div>

      <div className="dashboard-main">
        <div className="dash-top-row">
          <div>
            <h3>Hi, Coco Design 👋</h3>
            <p>Let&apos;s optimize your business with AI today!</p>
          </div>
          <div className="dash-meta">8:48:43 PM</div>
          <div className="dash-avatar" aria-hidden="true" />
          <div className="dash-calendar-mini">
            <div className="month">Mar 2025</div>
            <div className="calendar-grid">
              {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((d) => (
                <span key={`d-${d}`}>{d}</span>
              ))}
              {Array.from({ length: 7 }).map((_, i) => (
                <span key={`n-${i}`} className={i === 2 ? 'selected' : ''}>
                  {i + 4}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="dash-title-row">
          <h4>Your Sales & Analytics</h4>
          <button type="button" className="pill-btn soft small">
            Export as CSV
          </button>
        </div>

        <div className="dash-grid">
          <section className="metric-card lavender">
            <small>Available payout</small>
            <strong>$89.9K+</strong>
            <p>Payout of $6K will be available soon</p>
          </section>

          <section className="metric-card gray">
            <small>Today revenue</small>
            <strong>$49.9K+</strong>
            <p>Payout of $6K will be available soon</p>
          </section>

          <section className="visitors-card">
            <h5>Visitors</h5>
            {['Individual Target', 'Corporate Target', 'Foundation Target'].map((label, i) => (
              <div className="progress-row" key={label}>
                <div className="progress-label">
                  <span>{label}</span>
                  <b>{progress[i]}%</b>
                </div>
                <div className="progress-track">
                  <span style={{ width: `${progress[i]}%` }} />
                </div>
              </div>
            ))}
          </section>

          <section className="funnel-card">
            <div className="funnel-head">
              <div>
                <h5>Sales Funnel</h5>
                <p>Total view per month</p>
              </div>
              <button type="button" className="ghost-icon" aria-label="Adjust filters">
                <Sparkles size={15} />
              </button>
            </div>
            <div className="funnel-bars" aria-hidden="true">
              {bars.map((h, i) => (
                <div className={`bar ${i === 7 ? 'highlight' : ''}`} key={i} style={{ height: `${h}%` }}>
                  {i === 7 && <em>$450K</em>}
                </div>
              ))}
            </div>
            <div className="funnel-days">
              {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
                <span key={d}>{d}</span>
              ))}
            </div>
          </section>

          <section className="upgrade-card">
            <div className="upgrade-title">Upgrade To Pro</div>
            <p>Discover the benefits of an upgrade account.</p>
            <button type="button" className="pill-btn lilac wide small">
              Upgrade $10
            </button>
          </section>
        </div>
      </div>
    </div>
  )
}

function FloatingProductNav() {
  return (
    <div className="floating-product-nav" aria-label="Product navigation">
      <Brand dark />
      <nav>
        {navItems.map((item) => (
          <a href={`#${item.toLowerCase()}`} key={item}>
            {item}
          </a>
        ))}
      </nav>
      <button type="button" className="pill-btn lilac desktop-only">
        Try Opscale
      </button>
      <button type="button" className="mobile-icon-btn on-dark" aria-label="Open section menu">
        <Menu size={20} />
      </button>
    </div>
  )
}

function StatPanel() {
  return (
    <section className="stat-showcase" id="services">
      <Reveal className="section-head center" delay={0.02}>
        <p className="eyebrow">Operational visibility</p>
        <h2>Stay Ahead with that Drives Success</h2>
        <p className="subcopy">
          Monitor performance, automate repetitive work and make faster decisions with confidence.
        </p>
      </Reveal>

      <div className="stat-grid">
        <Reveal className="stat-left" delay={0.03}>
          <div className="big-figure-row">
            <div className="figure-block">
              <strong>98%</strong>
              <span>Faster automation</span>
            </div>
            <div className="figure-block">
              <strong>193.3K</strong>
              <span>Workflow runs</span>
            </div>
          </div>
          <div className="insight-card">
            <div>
              <h3>Real-Time Sales Insights</h3>
              <p>Track growth, payouts and team execution in one AI-assisted workspace.</p>
            </div>
            <div className="download-pill">
              <BarChart3 size={16} />
              Download Reports
            </div>
          </div>
        </Reveal>

        <Reveal className="stat-right" delay={0.08}>
          <div className="mini-stack-card">
            <div className="mini-line-chart">
              {Array.from({ length: 18 }).map((_, i) => (
                <span key={i} style={{ height: `${12 + ((i * 9) % 40)}px` }} />
              ))}
            </div>
            <div className="mini-grid-metrics">
              <div>
                <small>Conversion</small>
                <b>64%</b>
              </div>
              <div>
                <small>Qualified</small>
                <b>37%</b>
              </div>
              <div>
                <small>MRR Growth</small>
                <b>+18%</b>
              </div>
              <div>
                <small>Risk</small>
                <b>Low</b>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  )
}

function IntegrationsOrbit() {
  const nodes = [
    { top: '12%', left: '18%', label: 'CRM', hue: '#d8ff8c' },
    { top: '18%', right: '16%', label: 'BI', hue: '#c9bcff' },
    { top: '42%', left: '6%', label: 'Email', hue: '#bde8ff' },
    { top: '52%', right: '8%', label: 'Ads', hue: '#ffd8ab' },
    { bottom: '16%', left: '22%', label: 'Support', hue: '#d8ff8c' },
    { bottom: '14%', right: '20%', label: 'Payments', hue: '#c9bcff' },
  ] as const

  return (
    <section className="integrate-section" id="integrate">
      <Reveal className="section-head center" delay={0.02}>
        <p className="eyebrow">Integrations</p>
        <h2>Integrate. Automate. Elevate.</h2>
        <p className="subcopy">Connect your stack and orchestrate AI-powered workflows from a single control plane.</p>
      </Reveal>

      <Reveal className="orbit-stage" delay={0.06}>
        <div className="orbit-core">
          <span className="orbit-icon">
            <Cpu size={18} />
          </span>
          <div>
            <strong>Opscale AI</strong>
            <p>Workflow engine</p>
          </div>
        </div>

        <div className="orbit-line vertical" />
        <div className="orbit-line horizontal" />

        {nodes.map((node) => (
          <div className="orbit-node" key={node.label} style={{ ...node, background: node.hue }}>
            {node.label}
          </div>
        ))}
      </Reveal>
    </section>
  )
}

function FeatureGrid() {
  return (
    <section className="feature-section" id="features">
      <Reveal className="section-head center" delay={0.02}>
        <p className="eyebrow">Opscale Features</p>
        <h2>AI-Powered Features for Smarter Growth</h2>
        <p className="subcopy">Composable modules built for sales, ops and modern go-to-market teams.</p>
      </Reveal>

      <div className="feature-grid">
        {features.map((feature, i) => (
          <Reveal key={feature.title} delay={0.03 * (i % 3)}>
            <article className={`feature-card ${feature.tone}`}>
              <div className="feature-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.body}</p>
              <a href="#" aria-label={`Learn more about ${feature.title}`}>
                Learn more <ArrowRight size={15} />
              </a>
            </article>
          </Reveal>
        ))}
      </div>
    </section>
  )
}

function PricingSection() {
  return (
    <section className="pricing-section" id="pricing">
      <Reveal className="section-head center" delay={0.02}>
        <p className="eyebrow">Pricing</p>
        <h2>Smart Pricing for Every Plans</h2>
        <p className="subcopy">Start lean, expand with automation, and move to custom infrastructure when needed.</p>
      </Reveal>

      <div className="pricing-grid">
        {plans.map((plan, i) => (
          <Reveal key={plan.name} delay={0.05 * i}>
            <article className={`pricing-card ${plan.featured ? 'featured' : ''}`}>
              <div className="pricing-head">
                <div>
                  <h3>{plan.name}</h3>
                  {plan.badge ? <span className="badge">{plan.badge}</span> : null}
                </div>
                <p>
                  <strong>{plan.price}</strong>
                  {plan.period ? <span>{plan.period}</span> : null}
                </p>
              </div>

              <ul>
                {plan.points.map((point) => (
                  <li key={point}>
                    <span className="check-dot" />
                    {point}
                  </li>
                ))}
              </ul>

              <button type="button" className={`pill-btn ${plan.featured ? 'dark' : 'soft'} wide`}>
                {plan.featured ? 'Get Started' : 'Choose Plan'}
              </button>
            </article>
          </Reveal>
        ))}
      </div>

      <Reveal className="social-proof-row" delay={0.06}>
        <div className="proof-chip">
          <Shield size={16} /> Enterprise-grade security
        </div>
        <div className="proof-chip">
          <CircleDollarSign size={16} /> Transparent billing
        </div>
        <div className="proof-chip">
          <Users size={16} /> Trusted by industry leaders
        </div>
      </Reveal>
    </section>
  )
}

function WhyChooseSection() {
  const [openFaq, setOpenFaq] = useState(0)

  return (
    <section className="why-section" id="reviews">
      <Reveal className="why-card left" delay={0.03}>
        <div className="section-head left-align compact">
          <p className="eyebrow">Why Opscale</p>
          <h2>Why Opscale for Teams that Need Clarity</h2>
          <p className="subcopy">
            A calm interface for high-stakes operations: clear data, predictable workflows and AI that helps instead of distracts.
          </p>
        </div>

        <ul className="reason-list">
          <li>
            <span className="reason-icon"><Bot size={15} /></span>
            AI summaries that explain what changed and what to do next.
          </li>
          <li>
            <span className="reason-icon"><Workflow size={15} /></span>
            Workflow automation built into your day-to-day reporting.
          </li>
          <li>
            <span className="reason-icon"><Shield size={15} /></span>
            Secure infrastructure and role-based access for growing teams.
          </li>
          <li>
            <span className="reason-icon"><Database size={15} /></span>
            Centralized data model for analytics, CRM and execution tools.
          </li>
        </ul>
      </Reveal>

      <Reveal className="why-card faq-shell" delay={0.08}>
        <div className="section-head left-align compact">
          <p className="eyebrow">FAQ</p>
          <h2>Frequently Asked Questions</h2>
        </div>

        <div className="faq-list" id="faq">
          {faqs.map((item, i) => {
            const open = i === openFaq
            return (
              <div className={`faq-item ${open ? 'open' : ''}`} key={item.q}>
                <button type="button" onClick={() => setOpenFaq(open ? -1 : i)} aria-expanded={open}>
                  <span>{item.q}</span>
                  <ChevronDown size={16} />
                </button>
                <AnimatePresence initial={false}>
                  {open && (
                    <motion.div
                      className="faq-answer"
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2, ease: 'easeOut' }}
                    >
                      <p>{item.a}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )
          })}
        </div>
      </Reveal>
    </section>
  )
}

function TeamAndContact() {
  return (
    <section className="team-contact-section" id="services-extended">
      <Reveal className="team-card" delay={0.03}>
        <div className="section-head left-align compact">
          <p className="eyebrow">Meet the Team</p>
          <h2>Built by Operators, Designers and AI Product Builders</h2>
        </div>

        <div className="team-grid">
          {team.map((member) => (
            <article key={member.name} className="member-card">
              <div className="member-photo" style={{ background: `linear-gradient(140deg, ${member.accent}, #1b171a)` }} />
              <h3>{member.name}</h3>
              <p>{member.role}</p>
            </article>
          ))}
        </div>
      </Reveal>

      <Reveal className="contact-card" delay={0.08}>
        <div className="section-head left-align compact">
          <p className="eyebrow">Get in Touch</p>
          <h2>Book a Demo or Start Building Today</h2>
          <p className="subcopy">Tell us your goals and we&apos;ll suggest the fastest setup for your team.</p>
        </div>

        <div className="contact-grid">
          <label>
            Name
            <input type="text" placeholder="Your name" />
          </label>
          <label>
            Work email
            <input type="email" placeholder="you@company.com" />
          </label>
          <label>
            Company
            <input type="text" placeholder="Company" />
          </label>
          <label>
            Team size
            <input type="text" placeholder="10-50" />
          </label>
          <label className="full">
            What are you trying to improve?
            <textarea rows={4} placeholder="Lead routing, forecasting, reporting, automations..." />
          </label>
        </div>

        <div className="contact-meta-row">
          <a href="mailto:info@example.com">
            <Mail size={14} /> info@example.com
          </a>
          <a href="tel:+19876543210">
            <Phone size={14} /> +1 987 654 3210
          </a>
          <a href="#">
            <CalendarRange size={14} /> Get in touch
          </a>
        </div>

        <button type="button" className="pill-btn dark wide submit-btn">
          Start for free
        </button>
      </Reveal>
    </section>
  )
}

function Footer() {
  return (
    <footer className="site-footer">
      <Reveal className="footer-cta" delay={0.03}>
        <div>
          <p className="eyebrow">Ready to Scale?</p>
          <h2>Drive AI-Powered Growth with Opscale</h2>
          <p className="subcopy">Launch your analytics and automation layer with a premium workflow experience.</p>
        </div>
        <button type="button" className="pill-btn lilac footer-btn">
          Get Started <ArrowRight size={16} />
        </button>
      </Reveal>

      <div className="footer-bottom">
        <Brand dark />
        <div className="footer-links">
          {['Features', 'Integrate', 'Services', 'Pricing', 'FAQ', 'Contact'].map((link) => (
            <a href="#" key={link}>
              {link}
            </a>
          ))}
        </div>
        <p>Made with Framer-style UI simulation</p>
      </div>
    </footer>
  )
}

export default function App() {
  return (
    <div className="opscale-app">
      <TopHeader />

      <main>
        <section className="hero-section">
          <Reveal className="hero-inner" delay={0.02}>
            <div className="hero-badge">
              <span>NEW</span>
              Latest integration just arrived
            </div>
            <h1>Powering AI-Driven Growth with Opscale</h1>
            <p>
              We provide the tools and insights you need to enhance performance and achieve results.
            </p>
            <button type="button" className="pill-btn lilac hero-cta">
              Start for free
            </button>

            <motion.div
              className="hero-mockup-wrap"
              initial={{ opacity: 0, y: 18, scale: 0.985 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.6, ease: 'easeOut', delay: 0.12 }}
            >
              <DashboardMockup />
            </motion.div>
          </Reveal>
        </section>

        <section className="trust-band" aria-label="Trusted by leading enterprises">
          <div className="trust-copy">Trusted and adopted by industry-leading enterprises worldwide.</div>
          <div className="logo-row">
            {logos.map((logo, i) => (
              <span key={`${logo}-${i}`}>{logo}</span>
            ))}
          </div>
        </section>

        <div className="floating-nav-anchor">
          <FloatingProductNav />
        </div>

        <StatPanel />
        <IntegrationsOrbit />
        <FeatureGrid />
        <PricingSection />
        <WhyChooseSection />
        <TeamAndContact />
        <Footer />
      </main>
    </div>
  )
}
