import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import {
  ArrowUpRight,
  ChevronDown,
  Circle,
  Menu,
  MoveUpRight,
  X,
} from 'lucide-react'
import { type ReactNode, useState } from 'react'
import './App.css'

type ServiceCard = {
  title: string
  body: string
  accent: 'lime' | 'slate' | 'smoke'
}

type FitCard = {
  title: string
  bullets: string[]
  tone: 'light' | 'dark' | 'lime'
}

type TeamMember = {
  name: string
  role: string
  tone: string
}

type FAQ = {
  q: string
  a: string
}

const navItems = ['Services', 'Pricing', 'Case studies', 'Team', 'FAQ']

const services: ServiceCard[] = [
  {
    title: 'Business process automation',
    body: 'Remove repetitive work from operations using robust no-code and code-based automation systems.',
    accent: 'slate',
  },
  {
    title: "Integrate AI into your company's data",
    body: 'Connect internal data flows and decision-making layers so teams can use AI with confidence.',
    accent: 'smoke',
  },
  {
    title: 'AI-powered apps development',
    body: 'Design and ship focused AI products and internal tools that match real operational workflows.',
    accent: 'lime',
  },
  {
    title: 'AI automation consulting',
    body: 'Audit, roadmap and execution support to prioritize automation with measurable business impact.',
    accent: 'slate',
  },
  {
    title: 'Generative AI integration',
    body: 'Embed generative capabilities into products, CRM and support systems with model-aware UX.',
    accent: 'smoke',
  },
  {
    title: 'Ongoing Maintenance and Support',
    body: 'Continuous optimization, monitoring and iteration as workflows evolve with your team.',
    accent: 'slate',
  },
]

const fitCards: FitCard[] = [
  {
    title: 'Small business',
    bullets: ['Faster ops without hiring a large engineering team', 'Simple automation-first delivery'],
    tone: 'light',
  },
  {
    title: 'AI automation',
    bullets: ['Workflow orchestration', 'Data integration and decision loops'],
    tone: 'lime',
  },
  {
    title: 'Active products',
    bullets: ['Add AI features to a running product', 'Reduce time-to-value for experiments'],
    tone: 'dark',
  },
  {
    title: 'Startups',
    bullets: ['AI product from scratch', 'MVP to production transition support'],
    tone: 'light',
  },
]

const team: TeamMember[] = [
  { name: 'Rich Purnell', role: 'CEO', tone: '#1f1f22' },
  { name: 'Beth Johanssen', role: 'CTO', tone: '#232329' },
  { name: 'Chris Beck', role: 'Head of Data Engineering', tone: '#2c2c34' },
  { name: 'Mindy Park', role: 'CDO', tone: '#20252b' },
  { name: 'Mitch Henderson', role: 'Business Developer', tone: '#2a221f' },
  { name: 'Melissa Lewis', role: 'Product Strategist', tone: '#241f2f' },
]

const faqs: FAQ[] = [
  {
    q: 'What do you need from us to start?',
    a: 'A clear business goal, current workflow context and access to the systems you want to optimize. We handle discovery and technical scoping from there.',
  },
  {
    q: 'Can you work with existing teams and vendors?',
    a: 'Yes. We often collaborate with internal product, ops and engineering teams and build around existing tools instead of forcing full replacements.',
  },
  {
    q: 'Do you only build with no-code?',
    a: 'No. We use no-code when it accelerates delivery and custom code when reliability, performance or product depth requires it.',
  },
  {
    q: 'Do you offer ongoing support?',
    a: 'Yes. We provide maintenance, iteration and optimization as workflows scale and new AI opportunities appear.',
  },
]

const reveal = {
  hidden: { opacity: 0, y: 26 },
  show: { opacity: 1, y: 0 },
}

function Reveal({ children, delay = 0, className }: { children: ReactNode; delay?: number; className?: string }) {
  const reduce = useReducedMotion()
  if (reduce) return <div className={className}>{children}</div>

  return (
    <motion.div
      className={className}
      variants={reveal}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.18 }}
      transition={{ duration: 0.55, ease: 'easeOut', delay }}
    >
      {children}
    </motion.div>
  )
}

function Brand() {
  return (
    <div className="sanny-brand" aria-label="Sanny">
      <span>Sanny</span>
      <sup>®</sup>
    </div>
  )
}

function HeroPromoCard() {
  return (
    <motion.aside
      className="hero-promo-card"
      initial={{ rotate: 4, y: 10, opacity: 0 }}
      animate={{ rotate: 0, y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: 'easeOut', delay: 0.25 }}
    >
      <div className="promo-collage">
        <div className="promo-bg-figure">A<br />$99</div>
        <div className="promo-sticker center" />
        <div className="promo-sticker tl" />
        <div className="promo-sticker br" />
      </div>
      <div className="promo-foot">
        <h3>All Templates Bundle</h3>
        <p>
          <strong>$99</strong> <span>$285</span>
        </p>
      </div>
      <button className="promo-close" type="button" aria-label="Dismiss promo">
        <X size={14} />
      </button>
    </motion.aside>
  )
}

function MobilePromoCard() {
  return (
    <div className="mobile-promo-card" aria-hidden="true">
      <div className="promo-collage mobile">
        <div className="promo-bg-figure">A<br />$99</div>
        <div className="promo-sticker center" />
        <div className="promo-sticker tl" />
        <div className="promo-sticker br" />
      </div>
      <div className="promo-foot">
        <h3>All Templates Bundle</h3>
        <p>
          <strong>$99</strong> <span>$285</span>
        </p>
      </div>
    </div>
  )
}

function Header() {
  const [open, setOpen] = useState(false)

  return (
    <header className="sanny-header">
      <div className="sanny-header-shell">
        <div className="header-left">
          <Brand />
          <button type="button" className="icon-pill desktop-only" aria-label="Switch view">
            <MoveUpRight size={15} />
          </button>
        </div>

        <nav className="desktop-nav" aria-label="Primary">
          {navItems.map((item) => (
            <a href={`#${item.toLowerCase().replace(/\s+/g, '-')}`} key={item}>
              {item}
            </a>
          ))}
          <button type="button" className="buy-pill">
            Buy now
          </button>
        </nav>

        <div className="mobile-nav-actions">
          <button type="button" className="icon-pill" onClick={() => setOpen((v) => !v)} aria-label={open ? 'Close menu' : 'Open menu'}>
            {open ? <X size={16} /> : <Menu size={16} />}
          </button>
          <button type="button" className="buy-pill mobile-buy-pill">
            Buy now
          </button>
        </div>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            className="mobile-menu"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
          >
            {navItems.map((item) => (
              <a href={`#${item.toLowerCase().replace(/\s+/g, '-')}`} key={item} onClick={() => setOpen(false)}>
                {item}
              </a>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}

function HowStep({ index, title, body, highlight }: { index: string; title: string; body: string; highlight?: boolean }) {
  return (
    <article className={`how-step ${highlight ? 'highlight' : ''}`}>
      <div className="step-tag">Step {index}</div>
      <h3>{title}</h3>
      <p>{body}</p>
      <div className="step-lines" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
    </article>
  )
}

function ServiceVisual({ tone }: { tone: ServiceCard['accent'] }) {
  if (tone === 'lime') {
    return (
      <div className="service-visual lime">
        <div className="ring" />
        <div className="ring inner" />
        <div className="dot-lime" />
      </div>
    )
  }

  if (tone === 'smoke') {
    return (
      <div className="service-visual smoke">
        <div className="stack-card top" />
        <div className="stack-card middle" />
        <div className="stack-card bottom" />
      </div>
    )
  }

  return (
    <div className="service-visual slate">
      <div className="wave-row">
        <span />
        <span />
        <span />
      </div>
      <div className="wave-row alt">
        <span />
        <span />
        <span />
      </div>
    </div>
  )
}

export default function App() {
  const [openFaq, setOpenFaq] = useState(0)

  return (
    <div className="sanny-app">
      <main className="sanny-shell">
        <section className="hero-wrap">
          <Header />

          <Reveal className="hero-content" delay={0.03}>
            <div className="hero-grid">
              <div className="hero-main">
                <h1>
                  AI Services
                  <br />
                  for your Business
                  <br />
                  Growth
                </h1>
                <p>
                  We&apos;ll pump your company with AI. As a leading AI automation agency, we deliver top results with practical systems and strong execution.
                </p>

                <div className="hero-actions">
                  <button type="button" className="cta-lime">Subscribe now</button>
                  <button type="button" className="cta-ghost">Our services</button>
                  <div className="hero-trust-inline">
                    <span>Loved by founders worldwide</span>
                    <div className="avatars" aria-hidden="true">
                      <i />
                      <i />
                      <i />
                      <i />
                    </div>
                    <button type="button" className="icon-pill tiny" aria-label="Scroll down">
                      <ChevronDown size={13} />
                    </button>
                  </div>
                </div>
              </div>

              <div className="hero-side desktop-promo-slot">
                <HeroPromoCard />
              </div>
            </div>

            <div className="hero-bottom-fade" />
          </Reveal>

          <div className="hero-mobile-promo-slot">
            <MobilePromoCard />
          </div>
        </section>

        <section className="statement-section">
          <Reveal className="statement-card" delay={0.03}>
            <div className="statement-grid">
              <p className="statement-copy">
                Enhance your workflows to maximize performance and take effective control of your time. Focus on what truly matters while routine tasks run on autopilot with no-code and code-based solutions.
              </p>

              <div className="trusted-mini">
                <span>Trusted by high-growth teams</span>
                <div className="trusted-logos">
                  <b>Tarsca</b>
                  <b>OPJEA</b>
                  <em>theworks</em>
                </div>
              </div>
            </div>
          </Reveal>
        </section>

        <section className="how-section" id="case-studies">
          <Reveal className="section-label" delay={0.02}>
            <span>How it works?</span>
          </Reveal>

          <div className="how-grid">
            <Reveal delay={0.03}>
              <HowStep
                index="1"
                title="Subscribe"
                body="Choose a collaboration mode and a service scope that matches your current growth stage."
                highlight
              />
            </Reveal>
            <Reveal delay={0.06}>
              <HowStep
                index="2"
                title="Share your vision"
                body="We map your bottlenecks, priorities and opportunities to define the fastest path to impact."
              />
            </Reveal>
            <Reveal delay={0.09}>
              <HowStep
                index="3"
                title="Continuous results"
                body="We iterate, automate and optimize continuously as your team and product evolve."
              />
            </Reveal>
          </div>
        </section>

        <section className="services-section" id="services">
          <Reveal className="services-head" delay={0.02}>
            <div>
              <p className="micro-label">Services</p>
              <h2>AI solutions, delivered with speed and strong taste.</h2>
            </div>
            <div className="services-head-actions">
              <button type="button" className="cta-outline-dark">Plans & Pricing ↓</button>
              <button type="button" className="cta-outline-dark muted">guarantee ↓</button>
            </div>
          </Reveal>

          <div className="services-grid">
            {services.map((service, i) => (
              <Reveal key={service.title} delay={0.02 * (i % 3)}>
                <article className={`service-card ${service.accent}`}>
                  <ServiceVisual tone={service.accent} />
                  <h3>{service.title}</h3>
                  <p>{service.body}</p>
                  <a href="#" className="service-link">
                    Get started <ArrowUpRight size={14} />
                  </a>
                </article>
              </Reveal>
            ))}
          </div>
        </section>

        <section className="fit-section" id="pricing">
          <Reveal className="fit-head" delay={0.02}>
            <p className="micro-label">We are suitable for</p>
            <h2>Teams that want leverage, not just more software.</h2>
          </Reveal>

          <div className="fit-grid">
            {fitCards.map((card, i) => (
              <Reveal key={card.title} delay={0.03 * i}>
                <article className={`fit-card ${card.tone}`}>
                  <h3>{card.title}</h3>
                  <ul>
                    {card.bullets.map((bullet) => (
                      <li key={bullet}>
                        <Circle size={8} fill="currentColor" />
                        {bullet}
                      </li>
                    ))}
                  </ul>
                </article>
              </Reveal>
            ))}
          </div>
        </section>

        <section className="case-strip" id="team">
          <Reveal className="case-strip-card" delay={0.03}>
            <div className="case-media" aria-hidden="true" />
            <div className="case-body">
              <p className="micro-label">Case studies</p>
              <h2>From chaos to predictable delivery in 6 weeks.</h2>
              <p>
                We redesigned an operations flow, connected AI routing and cut repetitive manual work across the growth team.
              </p>
              <button type="button" className="cta-outline-light">Read case study</button>
            </div>
          </Reveal>
        </section>

        <section className="team-section">
          <Reveal className="team-head" delay={0.02}>
            <p className="micro-label">Team</p>
            <h2>People who ship real systems, not just decks.</h2>
          </Reveal>

          <div className="team-grid">
            {team.map((member, i) => (
              <Reveal key={member.name} delay={0.02 * (i % 3)}>
                <article className="team-card">
                  <div className="team-photo" style={{ background: `linear-gradient(145deg, ${member.tone}, #0a0a0c)` }} />
                  <h3>{member.name}</h3>
                  <p>{member.role}</p>
                </article>
              </Reveal>
            ))}
          </div>
        </section>

        <section className="faq-contact-section" id="faq">
          <Reveal className="faq-panel" delay={0.03}>
            <div className="panel-head">
              <p className="micro-label">FAQ</p>
              <h2>Questions, answered directly.</h2>
            </div>
            <div className="faq-list">
              {faqs.map((item, i) => {
                const open = openFaq === i
                return (
                  <div className={`faq-item ${open ? 'open' : ''}`} key={item.q}>
                    <button type="button" onClick={() => setOpenFaq(open ? -1 : i)} aria-expanded={open}>
                      <span>{item.q}</span>
                      <ChevronDown size={15} />
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

          <Reveal className="contact-panel" delay={0.08}>
            <div className="panel-head">
              <p className="micro-label">Book a call</p>
              <h2>Let’s talk about your bottlenecks.</h2>
            </div>

            <form className="contact-form" onSubmit={(e) => e.preventDefault()}>
              <label>
                Name
                <input type="text" placeholder="Melissa Lewis" />
              </label>
              <label>
                Email
                <input type="email" placeholder="hey@sanny.ai" />
              </label>
              <label>
                Company
                <input type="text" placeholder="Your company" />
              </label>
              <label>
                Project scope
                <input type="text" placeholder="AI automation consulting" />
              </label>
              <label className="full">
                Message
                <textarea rows={4} placeholder="Tell us what should be automated or improved." />
              </label>
              <button type="submit" className="cta-lime full-btn">
                Book call
              </button>
            </form>

            <div className="contact-links">
              <a href="mailto:hey@sanny.ai">hey@sanny.ai</a>
              <a href="#">LinkedIn</a>
              <a href="#">Twitter</a>
            </div>
          </Reveal>
        </section>

        <footer className="sanny-footer">
          <Reveal className="footer-shell" delay={0.03}>
            <div>
              <p className="micro-label">Ready?</p>
              <h2>Build your AI operations layer with confidence.</h2>
            </div>
            <div className="footer-actions">
              <button type="button" className="cta-lime">Get started</button>
              <button type="button" className="cta-ghost-dark">Book a call</button>
            </div>
          </Reveal>
        </footer>
      </main>
    </div>
  )
}
