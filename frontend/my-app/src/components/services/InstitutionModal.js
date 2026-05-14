import { useState, useEffect, useCallback } from "react";
import { sendMojterminContact, sendCrmContact, fetchUslugiCaptcha, sendUslugiContact } from "../../api/services";

const CRM_TOPICS = [
  { id: 1, label: "Пофалби" },
  { id: 2, label: "Поплаки" },
  { id: 3, label: "Прашања" },
];

const USLUGI_TICKET_TYPES = [
  { key: 1, label: "Услуга", isSubtype: false },
  { key: 2, label: "Институција", isSubtype: false },
  { key: 1, label: "Останато › Најава", isSubtype: true },
  { key: 2, label: "Останато › Плаќање", isSubtype: true },
  { key: 3, label: "Останато › Регистрација", isSubtype: true },
  { key: 4, label: "Останато › eID", isSubtype: true },
  { key: 5, label: "Останато › Друго", isSubtype: true },
];

const INSTITUTION_DETAILS = {
  uslugi: {
    fullName: "Министерство за информатичко општество и администрација",
    address: "Бул. Св. Климент Охридски 54, 1000 Скопје",
    phone: "+389 2 3200 800",
    email: "info@mioa.gov.mk",
    workingHours: "Пон–Пет, 08:30–16:30",
    mapQuery: "Ministry+of+Information+Society+Skopje+North+Macedonia",
  },
  mojtermin: {
    fullName: "Министерство за здравство на Македонија",
    address: "50-та Дивизија 14, 1000 Скопје",
    phone: "+389 2 3112 500",
    email: "contact@zdravstvo.gov.mk",
    workingHours: "Пон–Пет, 08:30–16:30",
    mapQuery: "Ministry+of+Health+Skopje+North+Macedonia+50+ta+divizija",
  },
  crm: {
    fullName: "Централен регистар на Северна Македонија",
    address: "Бул. Кузман Јосифовски Питу 1, 1000 Скопје",
    phone: "+389 2 3290 280",
    email: "info@crm.com.mk",
    workingHours: "Пон–Пет, 08:00–16:00",
    mapQuery: "Central+Registry+North+Macedonia+Skopje",
  },
  mon: {
    fullName: "Министерство за образование и наука",
    address: "Мито Хаџивасилев Јасмин бб, 1000 Скопје",
    phone: "+389 2 3117 896",
    email: "contact@mon.gov.mk",
    workingHours: "Пон–Пет, 08:30–16:30",
    mapQuery: "Ministry+of+Education+Skopje+North+Macedonia",
  },
  agencijaZaVrabotuvanje: {
    fullName: "Агенција за вработување на Република Северна Македонија",
    address: "Бул. Јане Сандански 114, 1000 Скопје",
    phone: "+389 2 3116 811",
    email: "info@av.gov.mk",
    workingHours: "Пон–Пет, 07:30–15:30",
    mapQuery: "Agency+for+Employment+Jane+Sandanski+Skopje+North+Macedonia",
  },
  katastar: {
    fullName: "Агенција за катастар на недвижности",
    address: "Бул. Александар Македонски бб, 1000 Скопје",
    phone: "+389 2 3103 400",
    email: "akn@katastar.gov.mk",
    workingHours: "Пон–Пет, 08:00–16:00",
    mapQuery: "Agency+for+Real+Estate+Cadastre+Skopje+North+Macedonia",
  },
};

const INPUT_STYLE = {
  width: "100%",
  background: "#f5f7ff",
  border: "1px solid rgba(99,102,241,0.2)",
  borderRadius: "0.625rem",
  padding: "0.6rem 0.875rem",
  fontSize: "0.875rem",
  color: "#1e293b",
  outline: "none",
};

function LightInput({ ...props }) {
  return (
    <input
      {...props}
      style={INPUT_STYLE}
      onFocus={e => { e.target.style.borderColor = "rgba(99,102,241,0.5)"; e.target.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.1)"; }}
      onBlur={e => { e.target.style.borderColor = "rgba(99,102,241,0.2)"; e.target.style.boxShadow = "none"; }}
    />
  );
}

function LightTextarea({ ...props }) {
  return (
    <textarea
      {...props}
      style={{ ...INPUT_STYLE, resize: "none" }}
      onFocus={e => { e.target.style.borderColor = "rgba(99,102,241,0.5)"; e.target.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.1)"; }}
      onBlur={e => { e.target.style.borderColor = "rgba(99,102,241,0.2)"; e.target.style.boxShadow = "none"; }}
    />
  );
}

function LightSelect({ children, ...props }) {
  return (
    <select
      {...props}
      style={{ ...INPUT_STYLE, cursor: "pointer" }}
      onFocus={e => { e.target.style.borderColor = "rgba(99,102,241,0.5)"; }}
      onBlur={e => { e.target.style.borderColor = "rgba(99,102,241,0.2)"; }}
    >
      {children}
    </select>
  );
}

function SubmitBtn({ loading, label, loadingLabel }) {
  return (
    <button
      type="submit"
      disabled={loading}
      className="w-full text-sm font-semibold py-2.5 rounded-xl text-white transition-all disabled:opacity-50"
      style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", boxShadow: "0 2px 10px rgba(99,102,241,0.35)" }}
      onMouseEnter={e => { if (!e.currentTarget.disabled) e.currentTarget.style.boxShadow = "0 4px 16px rgba(99,102,241,0.5)"; }}
      onMouseLeave={e => { e.currentTarget.style.boxShadow = "0 2px 10px rgba(99,102,241,0.35)"; }}
    >
      {loading ? loadingLabel : label}
    </button>
  );
}

function UslugiContactForm() {
  const [form, setForm] = useState({ ticketTypeKey: 1, ticketTypeIsSubtype: false, ticketTitle: "", ticketBody: "", userEmail: "" });
  const [captchaToken, setCaptchaToken] = useState(null);
  const [captchaUrl, setCaptchaUrl] = useState(null);
  const [captchaValue, setCaptchaValue] = useState("");
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadCaptcha = useCallback(async () => {
    try {
      const { blob, token } = await fetchUslugiCaptcha();
      const url = URL.createObjectURL(blob);
      setCaptchaUrl((prev) => { if (prev) URL.revokeObjectURL(prev); return url; });
      setCaptchaToken(token);
      setCaptchaValue("");
    } catch {}
  }, []);

  useEffect(() => { loadCaptcha(); }, [loadCaptcha]);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  const handleTypeChange = (e) => {
    const [key, isSubtype] = e.target.value.split("|");
    setForm((f) => ({ ...f, ticketTypeKey: Number(key), ticketTypeIsSubtype: isSubtype === "true" }));
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!captchaToken) return;
    setLoading(true); setStatus(null);
    try {
      await sendUslugiContact({ captcha_token: captchaToken, captcha_value: captchaValue, ticket_type_key: form.ticketTypeKey, ticket_type_is_subtype: form.ticketTypeIsSubtype, ticket_title: form.ticketTitle, ticket_body: form.ticketBody, user_email: form.userEmail || null });
      setStatus("success");
      setForm({ ticketTypeKey: 1, ticketTypeIsSubtype: false, ticketTitle: "", ticketBody: "", userEmail: "" });
      loadCaptcha();
    } catch (err) {
      setStatus(err?.response?.status === 400 ? "captcha_error" : "error");
      loadCaptcha();
    } finally { setLoading(false); }
  };

  return (
    <form onSubmit={submit} className="space-y-3">
      <h4 className="font-semibold text-sm" style={{ color: "#1e293b" }}>Постави прашање</h4>
      <div>
        <label className="text-xs mb-1 block" style={{ color: "#64748b" }}>Тип на прашање*</label>
        <LightSelect required value={`${form.ticketTypeKey}|${form.ticketTypeIsSubtype}`} onChange={handleTypeChange}>
          {USLUGI_TICKET_TYPES.map((t, i) => <option key={i} value={`${t.key}|${t.isSubtype}`}>{t.label}</option>)}
        </LightSelect>
      </div>
      <LightInput required placeholder="Наслов на прашањето*" value={form.ticketTitle} onChange={set("ticketTitle")} />
      <LightTextarea required placeholder="Повеќе детали за прашањето*" value={form.ticketBody} onChange={set("ticketBody")} rows={4} />
      <LightInput type="email" placeholder="Е-пошта за контакт (опционално)" value={form.userEmail} onChange={set("userEmail")} />
      <div className="space-y-2">
        <label className="text-xs block" style={{ color: "#64748b" }}>Внесете ги карактерите од сликата* (CAPTCHA)</label>
        <div className="flex items-center gap-3">
          {captchaUrl
            ? <img src={captchaUrl} alt="CAPTCHA" className="h-12 rounded-lg" style={{ border: "1px solid rgba(99,102,241,0.2)" }} />
            : <div className="h-12 w-24 rounded-lg animate-pulse" style={{ background: "rgba(99,102,241,0.08)" }} />
          }
          <button type="button" onClick={loadCaptcha} className="text-xs px-3 py-1.5 rounded-lg transition-all" style={{ border: "1px solid rgba(99,102,241,0.2)", color: "#6366f1" }}
            onMouseEnter={e => e.currentTarget.style.background = "rgba(99,102,241,0.07)"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
            ↺ Освежи
          </button>
        </div>
        <LightInput required placeholder="Внесете CAPTCHA" value={captchaValue} onChange={(e) => setCaptchaValue(e.target.value)} />
      </div>
      {status === "success" && <p className="text-xs" style={{ color: "#16a34a" }}>Прашањето е испратено успешно!</p>}
      {status === "captcha_error" && <p className="text-xs" style={{ color: "#dc2626" }}>Невалиден CAPTCHA. Обидете се повторно.</p>}
      {status === "error" && <p className="text-xs" style={{ color: "#dc2626" }}>Грешка при испраќање. Обидете се повторно.</p>}
      <SubmitBtn loading={loading} label="Испрати" loadingLabel="Испраќање..." />
    </form>
  );
}

function ContactForm() {
  const [form, setForm] = useState({ name: "", email: "", message: "" });
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault(); setLoading(true); setStatus(null);
    try { await sendMojterminContact(form.name, form.email, form.message); setStatus("success"); setForm({ name: "", email: "", message: "" }); }
    catch { setStatus("error"); }
    finally { setLoading(false); }
  };

  return (
    <form onSubmit={submit} className="space-y-3">
      <h4 className="font-semibold text-sm" style={{ color: "#1e293b" }}>Испрати порака</h4>
      <LightInput required placeholder="Целосно име" value={form.name} onChange={set("name")} />
      <LightInput required type="email" placeholder="Е-пошта" value={form.email} onChange={set("email")} />
      <LightTextarea required placeholder="Вашата порака" value={form.message} onChange={set("message")} rows={4} />
      {status === "success" && <p className="text-xs" style={{ color: "#16a34a" }}>Пораката е испратена успешно!</p>}
      {status === "error" && <p className="text-xs" style={{ color: "#dc2626" }}>Грешка при испраќање. Обидете се повторно.</p>}
      <SubmitBtn loading={loading} label="Испрати" loadingLabel="Испраќање..." />
    </form>
  );
}

function CrmContactForm() {
  const [form, setForm] = useState({ name: "", email: "", topic: 3, subject: "", message: "" });
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: field === "topic" ? Number(e.target.value) : e.target.value }));

  const submit = async (e) => {
    e.preventDefault(); setLoading(true); setStatus(null);
    try { await sendCrmContact(form.name, form.email, form.topic, form.subject, form.message); setStatus("success"); setForm({ name: "", email: "", topic: 3, subject: "", message: "" }); }
    catch (err) { setStatus(err?.response?.status === 412 ? "captcha" : "error"); }
    finally { setLoading(false); }
  };

  return (
    <form onSubmit={submit} className="space-y-3">
      <h4 className="font-semibold text-sm" style={{ color: "#1e293b" }}>Испрати порака</h4>
      <LightInput required placeholder="Целосно име" value={form.name} onChange={set("name")} />
      <LightInput required type="email" placeholder="Е-пошта" value={form.email} onChange={set("email")} />
      <LightSelect required value={form.topic} onChange={set("topic")}>
        {CRM_TOPICS.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
      </LightSelect>
      <LightInput required placeholder="Тема" value={form.subject} onChange={set("subject")} />
      <LightTextarea required placeholder="Вашата порака" value={form.message} onChange={set("message")} rows={4} />
      {status === "success" && <p className="text-xs" style={{ color: "#16a34a" }}>Пораката е испратена успешно!</p>}
      {status === "error" && <p className="text-xs" style={{ color: "#dc2626" }}>Грешка при испраќање. Обидете се повторно.</p>}
      {status === "captcha" && (
        <div className="rounded-xl px-4 py-3" style={{ background: "rgba(234,179,8,0.08)", border: "1px solid rgba(234,179,8,0.25)" }}>
          <p className="text-xs mb-1" style={{ color: "#ca8a04" }}>Потребна е CAPTCHA верификација на официјалниот сајт.</p>
          <a href="https://www.crm.com.mk/mk/za-tsrrsm/kontakt" target="_blank" rel="noreferrer" className="text-xs underline" style={{ color: "#6366f1" }}>
            Комплетирај на crm.com.mk →
          </a>
        </div>
      )}
      <SubmitBtn loading={loading} label="Испрати" loadingLabel="Испраќање..." />
    </form>
  );
}

export default function InstitutionModal({ institution, onClose }) {
  const details = INSTITUTION_DETAILS[institution.slug];

  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  if (!details) return null;

  const mapSrc = `https://maps.google.com/maps?q=${details.mapQuery}&output=embed&z=15`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(15,23,42,0.5)", backdropFilter: "blur(4px)" }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl"
        style={{ background: "#ffffff", boxShadow: "0 24px 64px rgba(99,102,241,0.2)", border: "1px solid rgba(99,102,241,0.15)" }}>

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 sticky top-0 rounded-t-2xl z-10"
          style={{ background: "#ffffff", borderBottom: "1px solid rgba(99,102,241,0.1)" }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(99,102,241,0.08)", color: "#6366f1" }}>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={1.75} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
              </svg>
            </div>
            <div>
              <h3 className="font-bold text-base" style={{ color: "#1e293b" }}>{institution.name}</h3>
              <p className="text-xs mt-0.5" style={{ color: "#94a3b8" }}>{details.fullName}</p>
            </div>
          </div>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-lg transition-all"
            style={{ color: "#94a3b8" }}
            onMouseEnter={e => { e.currentTarget.style.background = "rgba(99,102,241,0.07)"; e.currentTarget.style.color = "#6366f1"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#94a3b8"; }}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div className="px-6 py-5 space-y-5">
          {/* Map */}
          <div className="rounded-xl overflow-hidden h-48" style={{ border: "1px solid rgba(99,102,241,0.12)" }}>
            <iframe title="map" src={mapSrc} width="100%" height="100%" style={{ border: 0 }} loading="lazy" referrerPolicy="no-referrer-when-downgrade" />
          </div>

          {/* Contact info */}
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Адреса", value: details.address },
              { label: "Телефон", value: details.phone },
              { label: "Е-пошта", value: details.email },
              { label: "Работно време", value: details.workingHours },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-xl px-4 py-3"
                style={{ background: "#f5f7ff", border: "1px solid rgba(99,102,241,0.1)" }}>
                <p className="text-xs mb-1" style={{ color: "#94a3b8" }}>{label}</p>
                <p className="text-sm font-medium" style={{ color: "#1e293b" }}>{value}</p>
              </div>
            ))}
          </div>

          {/* Forms */}
          {institution.slug === "uslugi" && (
            <div className="pt-2" style={{ borderTop: "1px solid rgba(99,102,241,0.1)" }}>
              <UslugiContactForm />
            </div>
          )}
          {institution.slug === "mojtermin" && (
            <div className="pt-2" style={{ borderTop: "1px solid rgba(99,102,241,0.1)" }}>
              <ContactForm onClose={onClose} />
            </div>
          )}
          {institution.slug === "crm" && (
            <div className="pt-2" style={{ borderTop: "1px solid rgba(99,102,241,0.1)" }}>
              <CrmContactForm />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
