

import { useEffect, useMemo, useRef, useState } from "react";



const API_URL = "http://127.0.0.1:8000";

const MAX_UPLOAD_SIZE = 25 * 1024 * 1024;



const SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];



const SEVERITY_STYLES = {

  CRITICAL: "border-red-500/30 bg-red-500/10 text-red-400",

  HIGH: "border-orange-500/30 bg-orange-500/10 text-orange-400",

  MEDIUM: "border-yellow-500/30 bg-yellow-500/10 text-yellow-400",

  LOW: "border-blue-500/30 bg-blue-500/10 text-blue-400",

};



const SEVERITY_BAR_STYLES = {

  CRITICAL: "bg-red-500",

  HIGH: "bg-orange-500",

  MEDIUM: "bg-yellow-500",

  LOW: "bg-blue-500",

};



function Icon({ name, size = 18 }) {

  const common = {

    width: size,

    height: size,

    viewBox: "0 0 24 24",

    fill: "none",

    stroke: "currentColor",

    strokeWidth: 1.8,

    strokeLinecap: "round",

    strokeLinejoin: "round",

    "aria-hidden": true,

  };



  const paths = {

    shield: (

      <>

        <path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" />

        <path d="m9 12 2 2 4-4" />

      </>

    ),

    upload: (

      <>

        <path d="M12 16V4" />

        <path d="m7 9 5-5 5 5" />

        <path d="M20 16.5v3A1.5 1.5 0 0 1 18.5 21h-13A1.5 1.5 0 0 1 4 19.5v-3" />

      </>

    ),

    search: (

      <>

        <circle cx="10.8" cy="10.8" r="6.8" />

        <path d="m16 16 4 4" />

      </>

    ),

    download: (

      <>

        <path d="M12 3v12" />

        <path d="m7 10 5 5 5-5" />

        <path d="M4 20h16" />

      </>

    ),

    file: (

      <>

        <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9Z" />

        <path d="M13 2v7h7" />

        <path d="M8 15h8M8 18h8" />

      </>

    ),

    alert: (

      <>

        <path d="m10.3 3.9-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3.1l-8-14a2 2 0 0 0-3.4 0Z" />

        <path d="M12 9v4M12 17h.01" />

      </>

    ),

    check: <path d="m5 12 4 4L19 6" />,

    clock: (

      <>

        <circle cx="12" cy="12" r="9" />

        <path d="M12 7v5l3 2" />

      </>

    ),

    code: (

      <>

        <path d="m8 8-4 4 4 4M16 8l4 4-4 4M14 4l-4 16" />

      </>

    ),

    close: <path d="m18 6-12 12M6 6l12 12" />,

    refresh: (

      <>

        <path d="M20 7v5h-5" />

        <path d="M4 17v-5h5" />

        <path d="M5.6 9A7 7 0 0 1 18 6l2 6M4 12l2 6a7 7 0 0 0 12.4-3" />

      </>

    ),

    chevron: <path d="m9 18 6-6-6-6" />,

  };



  return <svg {...common}>{paths[name] || null}</svg>;

}



function SectionHeading({ eyebrow, title, description, action }) {

  return (

    <div className="flex flex-wrap items-end justify-between gap-4">

      <div>

        {eyebrow && (

          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-400">

            {eyebrow}

          </p>

        )}

        <h2 className="mt-1 text-xl font-semibold tracking-tight text-white">

          {title}

        </h2>

        {description && (

          <p className="mt-1 text-sm text-slate-500">{description}</p>

        )}

      </div>

      {action}

    </div>

  );

}



function MetricCard({ label, value, note, icon, accent = "emerald" }) {

  const accents = {

    emerald: "bg-emerald-500/10 text-emerald-400",

    orange: "bg-orange-500/10 text-orange-400",

    blue: "bg-blue-500/10 text-blue-400",

    red: "bg-red-500/10 text-red-400",

  };



  return (

    <div className="rounded-xl border border-white/[0.08] bg-[#101722] p-5">

      <div className="flex items-center justify-between gap-3">

        <p className="text-sm text-slate-400">{label}</p>

        <span className={`rounded-lg p-2 ${accents[accent]}`}>

          <Icon name={icon} size={17} />

        </span>

      </div>

      <p className="mt-4 text-3xl font-semibold tracking-tight text-white">

        {value ?? 0}

      </p>

      {note && <p className="mt-1 text-xs text-slate-500">{note}</p>}

    </div>

  );

}



function SeverityBadge({ severity }) {

  return (

    <span

      className={`inline-flex rounded-md border px-2 py-1 text-[11px] font-semibold tracking-wide ${

        SEVERITY_STYLES[severity] || "border-slate-700 text-slate-400"

      }`}

    >

      {severity || "UNKNOWN"}

    </span>

  );

}



function EngineStatus({ name, status }) {

  const normalized = String(status || "unknown").toLowerCase();



  const styles = {

    completed: "bg-emerald-400",

    partial: "bg-yellow-400",

    unavailable: "bg-red-400",

    failed: "bg-red-400",

    unknown: "bg-slate-500",

  };



  const labels = {

    completed: "Completed",

    partial: "Partial",

    unavailable: "Unavailable",

    failed: "Failed",

    unknown: "Unknown",

  };



  return (

    <div className="flex items-center justify-between gap-3 border-b border-white/[0.06] py-3 last:border-0">

      <span className="text-sm text-slate-300">{name}</span>

      <span className="flex items-center gap-2 text-xs text-slate-400">

        <span className={`h-2 w-2 rounded-full ${styles[normalized] || styles.unknown}`} />

        {labels[normalized] || normalized}

      </span>

    </div>

  );

}



function App() {

  const fileInput = useRef(null);



  const [apiStatus, setApiStatus] = useState("checking");

  const [selectedFile, setSelectedFile] = useState(null);

  const [report, setReport] = useState(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [dragging, setDragging] = useState(false);



  const [searchTerm, setSearchTerm] = useState("");

  const [severityFilter, setSeverityFilter] = useState("ALL");

  const [categoryFilter, setCategoryFilter] = useState("ALL");

  const [sourceFilter, setSourceFilter] = useState("ALL");

  const [selectedFinding, setSelectedFinding] = useState(null);



  useEffect(() => {

    let active = true;



    async function checkBackend() {

      try {

        const response = await fetch(`${API_URL}/health`);



        if (!response.ok) {

          throw new Error("Backend unavailable");

        }



        const data = await response.json();



        if (active) {

          setApiStatus(data.status === "healthy" ? "connected" : "offline");

        }

      } catch {

        if (active) setApiStatus("offline");

      }

    }



    checkBackend();

    const interval = setInterval(checkBackend, 10000);



    return () => {

      active = false;

      clearInterval(interval);

    };

  }, []);



  async function handleScan(file) {

    if (!file || loading) return;



    if (!file.name.toLowerCase().endsWith(".zip")) {

      setError("Please select a ZIP archive.");

      return;

    }



    if (file.size === 0) {

      setError("The selected ZIP archive is empty.");

      return;

    }



    if (file.size > MAX_UPLOAD_SIZE) {

      setError("The maximum upload size is 25 MB.");

      return;

    }



    setSelectedFile(file);

    setReport(null);

    setSelectedFinding(null);

    setError("");

    setSearchTerm("");

    setSeverityFilter("ALL");

    setCategoryFilter("ALL");

    setSourceFilter("ALL");

    setLoading(true);



    const formData = new FormData();

    formData.append("file", file);



    try {

      const response = await fetch(`${API_URL}/scan/upload`, {

        method: "POST",

        body: formData,

      });



      const data = await response.json().catch(() => ({}));



      if (!response.ok) {

        throw new Error(data.detail || "The scan could not be completed.");

      }



      setReport(data);

    } catch (scanError) {

      setError(

        scanError.message ||

          "Unable to connect to the CipherSight backend."

      );

    } finally {

      setLoading(false);

    }

  }



  const findings = useMemo(() => report?.findings ?? [], [report?.findings]);

  const summary = useMemo(() => report?.summary ?? {}, [report?.summary]);

  const severity = useMemo(
    () => report?.severity_distribution ?? {},
    [report?.severity_distribution]
  );

  const categories = useMemo(
    () => report?.category_distribution ?? {},
    [report?.category_distribution]
  );

  const sources = useMemo(
    () => report?.source_distribution ?? {},
    [report?.source_distribution]
  );

  const engines = useMemo(() => report?.engines ?? {}, [report?.engines]);



  const categoryOptions = useMemo(

    () => Object.keys(categories).sort(),

    [categories]

  );



  const sourceOptions = useMemo(

    () => Object.keys(sources).sort(),

    [sources]

  );



  const filteredFindings = useMemo(() => {

    const query = searchTerm.trim().toLowerCase();



    return findings.filter((finding) => {

      const matchesSeverity =

        severityFilter === "ALL" || finding.severity === severityFilter;



      const matchesCategory =

        categoryFilter === "ALL" || finding.category === categoryFilter;



      const findingSources = finding.sources || [];

      const matchesSource =

        sourceFilter === "ALL" || findingSources.includes(sourceFilter);



      const searchable = [

        finding.rule_id,

        finding.rule_ids?.join(" "),

        finding.category,

        finding.file,

        finding.evidence,

        finding.description,

        finding.remediation,

        findingSources.join(" "),

      ]

        .join(" ")

        .toLowerCase();



      return (

        matchesSeverity &&

        matchesCategory &&

        matchesSource &&

        searchable.includes(query)

      );

    });

  }, [

    findings,

    searchTerm,

    severityFilter,

    categoryFilter,

    sourceFilter,

  ]);



  function downloadReport() {

    if (!report) return;



    const blob = new Blob([JSON.stringify(report, null, 2)], {

      type: "application/json",

    });



    const url = URL.createObjectURL(blob);

    const anchor = document.createElement("a");



    anchor.href = url;

    anchor.download = `${report.project || "ciphersight"}-security-report.json`;

    document.body.appendChild(anchor);

    anchor.click();

    anchor.remove();



    URL.revokeObjectURL(url);

  }



  function resetFilters() {

    setSearchTerm("");

    setSeverityFilter("ALL");

    setCategoryFilter("ALL");

    setSourceFilter("ALL");

  }



  const statusConfig = {

    checking: {

      label: "Checking API",

      dot: "bg-yellow-400",

      style: "border-yellow-500/20 bg-yellow-500/10 text-yellow-400",

    },

    connected: {

      label: "API Connected",

      dot: "bg-emerald-400",

      style: "border-emerald-500/20 bg-emerald-500/10 text-emerald-400",

    },

    offline: {

      label: "API Offline",

      dot: "bg-red-400",

      style: "border-red-500/20 bg-red-500/10 text-red-400",

    },

  };



  const currentStatus = statusConfig[apiStatus];



  const riskLevel = report?.risk_assessment?.risk_level || "UNKNOWN";

  const riskStyle =

    riskLevel === "CRITICAL" || riskLevel === "HIGH"

      ? "text-orange-400"

      : riskLevel === "MEDIUM"

        ? "text-yellow-400"

        : riskLevel === "LOW"

          ? "text-emerald-400"

          : "text-slate-400";



  const generatedAt = report?.generated_at

    ? new Date(report.generated_at).toLocaleString()

    : null;



  return (

    <div className="min-h-screen bg-[#090d13] text-slate-100">

      <div className="flex min-h-screen">

        <aside className="hidden w-64 shrink-0 flex-col border-r border-white/[0.07] bg-[#0d131c] p-6 md:flex">

          <div className="mb-12 flex items-center gap-3">

            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-400/20 bg-emerald-400/10 text-emerald-400">

              <Icon name="shield" size={22} />

            </div>

            <div>

              <h1 className="text-lg font-bold tracking-wide text-white">

                CipherSight

              </h1>

              <p className="text-xs text-slate-500">

                Source Code Security

              </p>

            </div>

          </div>



          <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-600">

            Workspace

          </p>



          <div className="flex items-center gap-3 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm font-medium text-emerald-400">

            <Icon name="code" size={17} />

            Overview

          </div>



          <div className="mt-3 flex items-center gap-3 px-4 py-3 text-sm text-slate-500">

            <Icon name="alert" size={17} />

            Security findings

          </div>



          <div className="flex items-center gap-3 px-4 py-3 text-sm text-slate-500">

            <Icon name="file" size={17} />

            Scan reports

          </div>



          <div className="mt-auto border-t border-white/[0.07] pt-5">

            <p className="text-[10px] font-bold tracking-[0.2em] text-slate-600">

              CIPHERSIGHT

            </p>

            <p className="mt-1 text-xs text-slate-500">

              Version 1.0 · Development

            </p>

          </div>

        </aside>



        <main className="min-w-0 flex-1">

          <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.07] px-5 py-5 sm:px-8 lg:px-10">

            <div>

              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">

                Workspace / Overview

              </p>

              <h2 className="mt-1 text-xl font-semibold text-white">

                Security Dashboard

              </h2>

            </div>



            <div

              className={`flex items-center gap-2 rounded-full border px-3 py-2 text-xs ${currentStatus.style}`}

            >

              <span className={`h-2 w-2 rounded-full ${currentStatus.dot}`} />

              {currentStatus.label}

            </div>

          </header>



          <div className="mx-auto max-w-[1500px] space-y-9 p-5 sm:p-8 lg:p-10">

            <section className="flex flex-wrap items-end justify-between gap-5">

              <div>

                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">

                  Application security analysis

                </p>

                <h1 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">

                  Inspect. Detect. Secure.

                </h1>

                <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">

                  Analyze source code for potential security vulnerabilities.

                  Identify risky patterns and review actionable remediation

                  guidance.

                </p>

              </div>



              {report && (

                <button

                  onClick={downloadReport}

                  className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-[#121b27] px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:border-emerald-500/40 hover:text-emerald-400"

                >

                  <Icon name="download" size={16} />

                  Export JSON

                </button>

              )}

            </section>



            <section className="rounded-2xl border border-white/[0.08] bg-[#101722] p-5 sm:p-7">

              <div className="mb-6">

                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">

                  Project scanner

                </p>

                <h3 className="mt-2 text-lg font-semibold text-white">

                  Analyze a project

                </h3>

                <p className="mt-1 text-sm text-slate-500">

                  Upload a ZIP archive containing your source code.

                </p>

              </div>



              <div

                role="button"

                tabIndex={loading ? -1 : 0}

                aria-label="Choose a ZIP archive to scan"

                onKeyDown={(event) => {

                  if (

                    !loading &&

                    (event.key === "Enter" || event.key === " ")

                  ) {

                    event.preventDefault();

                    fileInput.current?.click();

                  }

                }}

                onDragOver={(event) => {

                  event.preventDefault();

                  if (!loading) setDragging(true);

                }}

                onDragLeave={(event) => {

                  event.preventDefault();

                  setDragging(false);

                }}

                onDrop={(event) => {

                  event.preventDefault();

                  setDragging(false);

                  if (!loading) handleScan(event.dataTransfer.files[0]);

                }}

                onClick={() => {

                  if (!loading) fileInput.current?.click();

                }}

                className={`cursor-pointer rounded-xl border border-dashed p-8 text-center outline-none transition sm:p-10 ${

                  dragging

                    ? "border-emerald-400 bg-emerald-500/10"

                    : "border-slate-700 bg-[#0b111a] hover:border-emerald-500/50 focus:border-emerald-400"

                } ${loading ? "cursor-not-allowed opacity-60" : ""}`}

              >

                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-emerald-500/20 bg-emerald-500/10 text-emerald-400">

                  <Icon name="upload" size={25} />

                </div>



                <p className="mt-4 font-medium text-white">

                  {selectedFile

                    ? selectedFile.name

                    : "Drop your project ZIP here"}

                </p>

                <p className="mt-2 text-sm text-slate-500">

                  or click to browse files

                </p>

                <p className="mt-4 text-xs text-slate-600">

                  ZIP archives · Maximum 25 MB

                </p>



                <input

                  ref={fileInput}

                  type="file"

                  accept=".zip,application/zip"

                  className="hidden"

                  disabled={loading}

                  onChange={(event) => {

                    handleScan(event.target.files?.[0]);

                    event.target.value = "";

                  }}

                />

              </div>



              {error && (

                <div className="mt-4 flex items-start gap-3 rounded-lg border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-300">

                  <Icon name="alert" size={18} />

                  <p>{error}</p>

                </div>

              )}



              {loading && (

                <div className="mt-5 flex items-center gap-3 text-sm text-emerald-400">

                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-400 border-t-transparent" />

                  Analyzing source code. This may take a moment...

                </div>

              )}

            </section>



            {report && (

              <>

                <section className="space-y-5">

                  <SectionHeading

                    eyebrow="Analysis results"

                    title="Scan overview"

                    description={`Project: ${report.project || "Unknown project"}`}

                    action={

                      <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5 text-xs text-emerald-400">

                        <Icon name="check" size={14} />

                        Report generated

                      </span>

                    }

                  />



                  <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

                    <MetricCard

                      label="Total findings"

                      value={summary.total_findings}

                      note="Unique detected findings"

                      icon="alert"

                      accent="orange"

                    />

                    <MetricCard

                      label="Files scanned"

                      value={summary.files_scanned}

                      note="Source files analyzed"

                      icon="file"

                      accent="blue"

                    />

                    <MetricCard

                      label="Affected files"

                      value={summary.files_with_findings}

                      note="Files containing findings"

                      icon="code"

                      accent="orange"

                    />

                    <MetricCard

                      label="Scan errors"

                      value={summary.total_errors}

                      note={`${summary.files_skipped || 0} files skipped`}

                      icon="alert"

                      accent="red"

                    />

                  </div>

                </section>



                <section className="grid gap-5 lg:grid-cols-3">

                  <div className="rounded-xl border border-white/[0.08] bg-[#101722] p-6">

                    <p className="text-sm text-slate-400">

                      Overall risk assessment

                    </p>

                    <p className={`mt-4 text-3xl font-bold ${riskStyle}`}>

                      {riskLevel}

                    </p>

                    <p className="mt-2 text-xs text-slate-500">

                      Highest severity:{" "}

                      {report.risk_assessment?.highest_severity || "Unknown"}

                    </p>

                    <div className="mt-5 border-t border-white/[0.07] pt-4">

                      <p className="text-xs text-slate-500">

                        Generated at

                      </p>

                      <p className="mt-1 text-xs text-slate-300">

                        {generatedAt || "Not available"}

                      </p>

                    </div>

                  </div>



                  <div className="rounded-xl border border-white/[0.08] bg-[#101722] p-6 lg:col-span-2">

                    <h3 className="font-semibold text-white">

                      Severity distribution

                    </h3>

                    <p className="mt-1 text-xs text-slate-500">

                      Findings grouped by severity level

                    </p>



                    <div className="mt-6 space-y-5">

                      {SEVERITIES.map((level) => {

                        const count = severity[level] || 0;

                        const percentage = summary.total_findings

                          ? (count / summary.total_findings) * 100

                          : 0;



                        return (

                          <div key={level}>

                            <div className="mb-2 flex justify-between text-sm">

                              <span className="text-slate-400">{level}</span>

                              <span className="font-medium text-slate-200">

                                {count}

                              </span>

                            </div>

                            <div className="h-2 overflow-hidden rounded-full bg-slate-800">

                              <div

                                className={`h-full rounded-full transition-all ${SEVERITY_BAR_STYLES[level]}`}

                                style={{ width: `${percentage}%` }}

                              />

                            </div>

                          </div>

                        );

                      })}

                    </div>

                  </div>

                </section>



                <section className="grid gap-5 lg:grid-cols-2">

                  <div className="rounded-xl border border-white/[0.08] bg-[#101722] p-6">

                    <h3 className="font-semibold text-white">

                      Category distribution

                    </h3>

                    <div className="mt-4 space-y-3">

                      {Object.entries(categories).length === 0 && (

                        <p className="text-sm text-slate-500">

                          No category data available.

                        </p>

                      )}

                      {Object.entries(categories)

                        .sort((a, b) => b[1] - a[1])

                        .map(([category, count]) => (

                          <div

                            key={category}

                            className="flex items-center justify-between gap-3 border-b border-white/[0.05] pb-3 last:border-0"

                          >

                            <span className="text-sm text-slate-300">

                              {category}

                            </span>

                            <span className="rounded-md bg-white/[0.05] px-2.5 py-1 text-xs text-slate-300">

                              {count}

                            </span>

                          </div>

                        ))}

                    </div>

                  </div>



                  <div className="rounded-xl border border-white/[0.08] bg-[#101722] p-6">

                    <h3 className="font-semibold text-white">

                      Scanner engines

                    </h3>

                    <p className="mt-1 text-xs text-slate-500">

                      Execution status for each analysis engine

                    </p>

                    <div className="mt-3">

                      <EngineStatus

                        name="Python AST"

                        status={engines.python_ast}

                      />

                      <EngineStatus

                        name="Semgrep"

                        status={engines.semgrep}

                      />

                    </div>

                    <div className="mt-4 border-t border-white/[0.06] pt-4">

                      <p className="mb-2 text-xs text-slate-500">

                        Detection sources

                      </p>

                      {Object.entries(sources).map(([source, count]) => (

                        <div

                          key={source}

                          className="flex justify-between py-1 text-xs"

                        >

                          <span className="text-slate-400">{source}</span>

                          <span className="text-slate-300">{count}</span>

                        </div>

                      ))}

                    </div>

                  </div>

                </section>



                <section className="overflow-hidden rounded-xl border border-white/[0.08] bg-[#101722]">

                  <div className="border-b border-white/[0.07] p-5 sm:p-6">

                    <SectionHeading

                      title="Security findings"

                      description="Search, filter, and inspect detected vulnerabilities."

                      action={

                        <span className="text-xs text-slate-500">

                          {filteredFindings.length} of {findings.length} shown

                        </span>

                      }

                    />

                  </div>



                  <div className="grid gap-3 border-b border-white/[0.07] p-4 sm:grid-cols-2 xl:grid-cols-4">

                    <div className="relative">

                      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">

                        <Icon name="search" size={16} />

                      </span>

                      <input

                        type="search"

                        placeholder="Search findings..."

                        value={searchTerm}

                        onChange={(event) => setSearchTerm(event.target.value)}

                        className="w-full rounded-lg border border-white/10 bg-[#0b111a] py-2.5 pl-9 pr-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-emerald-500/50"

                      />

                    </div>



                    <select

                      value={severityFilter}

                      onChange={(event) =>

                        setSeverityFilter(event.target.value)

                      }

                      className="rounded-lg border border-white/10 bg-[#0b111a] px-3 py-2.5 text-sm text-slate-300 outline-none focus:border-emerald-500/50"

                    >

                      <option value="ALL">All severities</option>

                      {SEVERITIES.map((level) => (

                        <option key={level} value={level}>

                          {level}

                        </option>

                      ))}

                    </select>



                    <select

                      value={categoryFilter}

                      onChange={(event) =>

                        setCategoryFilter(event.target.value)

                      }

                      className="rounded-lg border border-white/10 bg-[#0b111a] px-3 py-2.5 text-sm text-slate-300 outline-none focus:border-emerald-500/50"

                    >

                      <option value="ALL">All categories</option>

                      {categoryOptions.map((category) => (

                        <option key={category} value={category}>

                          {category}

                        </option>

                      ))}

                    </select>



                    <select

                      value={sourceFilter}

                      onChange={(event) => setSourceFilter(event.target.value)}

                      className="rounded-lg border border-white/10 bg-[#0b111a] px-3 py-2.5 text-sm text-slate-300 outline-none focus:border-emerald-500/50"

                    >

                      <option value="ALL">All sources</option>

                      {sourceOptions.map((source) => (

                        <option key={source} value={source}>

                          {source}

                        </option>

                      ))}

                    </select>

                  </div>



                  <div className="overflow-x-auto">

                    <table className="w-full min-w-[700px] text-left text-sm">

                      <thead className="bg-[#0b111a] text-[10px] uppercase tracking-wider text-slate-500">

                        <tr>

                          <th className="px-5 py-4 font-semibold">Rule</th>

                          <th className="px-5 py-4 font-semibold">Category</th>

                          <th className="px-5 py-4 font-semibold">File / Line</th>

                          <th className="px-5 py-4 font-semibold">Severity</th>

                          <th className="px-5 py-4 font-semibold">Sources</th>

                          <th className="px-5 py-4 font-semibold">Details</th>

                        </tr>

                      </thead>

                      <tbody className="divide-y divide-white/[0.05]">

                        {filteredFindings.map((finding, index) => (

                          <tr

                            key={`${finding.rule_id}-${finding.file}-${finding.line}-${index}`}

                            className={`transition hover:bg-white/[0.025] ${

                              selectedFinding === finding

                                ? "bg-emerald-500/[0.04]"

                                : ""

                            }`}

                          >

                            <td className="px-5 py-4 font-mono text-xs text-emerald-400">

                              {finding.rule_id}

                            </td>

                            <td className="px-5 py-4 text-slate-300">

                              {finding.category}

                            </td>

                            <td className="px-5 py-4 font-mono text-xs text-slate-400">

                              {finding.file}:{finding.line}

                            </td>

                            <td className="px-5 py-4">

                              <SeverityBadge severity={finding.severity} />

                            </td>

                            <td className="px-5 py-4 text-xs text-slate-400">

                              {(finding.sources || []).join(", ") || "Unknown"}

                            </td>

                            <td className="px-5 py-4">

                              <button

                                onClick={() => setSelectedFinding(finding)}

                                className="inline-flex items-center gap-1 text-xs font-medium text-emerald-400 hover:text-emerald-300"

                              >

                                Inspect <Icon name="chevron" size={14} />

                              </button>

                            </td>

                          </tr>

                        ))}



                        {filteredFindings.length === 0 && (

                          <tr>

                            <td

                              colSpan="6"

                              className="px-5 py-12 text-center text-sm text-slate-500"

                            >

                              No findings match the selected filters.

                              <button

                                onClick={resetFilters}

                                className="ml-2 text-emerald-400 hover:text-emerald-300"

                              >

                                Clear filters

                              </button>

                            </td>

                          </tr>

                        )}

                      </tbody>

                    </table>

                  </div>

                </section>



                {selectedFinding && (

                  <section className="rounded-xl border border-emerald-500/20 bg-[#101722] p-5 sm:p-7">

                    <div className="flex flex-wrap items-start justify-between gap-4">

                      <div>

                        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-400">

                          Finding details

                        </p>

                        <h3 className="mt-2 text-xl font-semibold text-white">

                          {selectedFinding.category}

                        </h3>

                        <p className="mt-1 font-mono text-xs text-slate-500">

                          {selectedFinding.rule_id} · {selectedFinding.file}:

                          {selectedFinding.line}

                        </p>

                      </div>

                      <div className="flex items-center gap-3">

                        <SeverityBadge severity={selectedFinding.severity} />

                        <button

                          onClick={() => setSelectedFinding(null)}

                          aria-label="Close finding details"

                          className="rounded-lg border border-white/10 p-2 text-slate-400 hover:text-white"

                        >

                          <Icon name="close" size={17} />

                        </button>

                      </div>

                    </div>



                    <div className="mt-6 grid gap-5 lg:grid-cols-2">

                      <div>

                        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">

                          Description

                        </p>

                        <p className="mt-2 text-sm leading-6 text-slate-300">

                          {selectedFinding.description ||

                            "No description available."}

                        </p>



                        <p className="mt-5 text-xs font-semibold uppercase tracking-wider text-slate-500">

                          Detection sources

                        </p>

                        <div className="mt-2 flex flex-wrap gap-2">

                          {(selectedFinding.sources || []).map((source) => (

                            <span

                              key={source}

                              className="rounded-md border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-slate-300"

                            >

                              {source}

                            </span>

                          ))}

                        </div>

                      </div>



                      <div>

                        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">

                          Source evidence

                        </p>

                        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words rounded-lg border border-white/[0.06] bg-[#090d13] p-4 font-mono text-sm leading-6 text-orange-300">

                          {selectedFinding.evidence || "No evidence available."}

                        </pre>



                        <p className="mt-5 text-xs font-semibold uppercase tracking-wider text-emerald-400">

                          Recommended remediation

                        </p>

                        <p className="mt-2 text-sm leading-6 text-slate-300">

                          {selectedFinding.remediation ||

                            "No remediation guidance available."}

                        </p>

                      </div>

                    </div>



                    {(selectedFinding.cwe?.length > 0 ||

                      selectedFinding.owasp?.length > 0 ||

                      selectedFinding.references?.length > 0) && (

                      <div className="mt-6 grid gap-5 border-t border-white/[0.07] pt-5 md:grid-cols-2">

                        {selectedFinding.cwe?.length > 0 && (

                          <div>

                            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">

                              CWE references

                            </p>

                            <ul className="mt-2 space-y-1 text-sm text-slate-300">

                              {selectedFinding.cwe.map((item) => (

                                <li key={item}>{item}</li>

                              ))}

                            </ul>

                          </div>

                        )}



                        {selectedFinding.owasp?.length > 0 && (

                          <div>

                            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">

                              OWASP references

                            </p>

                            <ul className="mt-2 space-y-1 text-sm text-slate-300">

                              {selectedFinding.owasp.map((item) => (

                                <li key={item}>{item}</li>

                              ))}

                            </ul>

                          </div>

                        )}



                        {selectedFinding.references?.length > 0 && (

                          <div className="md:col-span-2">

                            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">

                              Further reading

                            </p>

                            <ul className="mt-2 space-y-2">

                              {selectedFinding.references.map((reference) => (

                                <li key={reference}>

                                  <a

                                    href={reference}

                                    target="_blank"

                                    rel="noreferrer"

                                    className="break-all text-sm text-emerald-400 hover:underline"

                                  >

                                    {reference}

                                  </a>

                                </li>

                              ))}

                            </ul>

                          </div>

                        )}

                      </div>

                    )}

                  </section>

                )}



                {report.errors?.length > 0 && (

                  <section className="rounded-xl border border-yellow-500/20 bg-yellow-500/[0.04] p-5 sm:p-6">

                    <div className="flex items-center gap-3">

                      <span className="rounded-lg bg-yellow-500/10 p-2 text-yellow-400">

                        <Icon name="alert" size={18} />

                      </span>

                      <div>

                        <h3 className="font-semibold text-yellow-400">

                          Scan warnings and errors

                        </h3>

                        <p className="text-xs text-slate-500">

                          {report.errors.length} diagnostic(s) reported

                        </p>

                      </div>

                    </div>



                    <div className="mt-4 space-y-3">

                      {report.errors.map((item, index) => (

                        <div

                          key={`${item.file}-${index}`}

                          className="rounded-lg border border-white/[0.06] bg-[#0b111a] p-4"

                        >

                          <p className="text-sm font-medium text-slate-200">

                            {item.file || "Scanner"}

                          </p>

                          <p className="mt-2 whitespace-pre-wrap break-words text-xs leading-5 text-slate-400">

                            {item.error || "Unknown scan error"}

                          </p>

                          {item.sources?.length > 0 && (

                            <p className="mt-2 text-[11px] text-slate-500">

                              Sources: {item.sources.join(", ")}

                            </p>

                          )}

                        </div>

                      ))}

                    </div>

                  </section>

                )}

              </>

            )}



            {!report && !loading && (

              <div className="rounded-xl border border-dashed border-white/[0.08] py-12 text-center">

                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-white/[0.04] text-slate-500">

                  <Icon name="file" size={22} />

                </div>

                <p className="mt-4 text-sm font-medium text-slate-300">

                  No scan report yet

                </p>

                <p className="mt-1 text-sm text-slate-500">

                  Upload a project ZIP to generate a security report.

                </p>

              </div>

            )}



            <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.07] pt-6 text-xs text-slate-600">

              <span>CipherSight · Source Code Security Analyzer</span>

              <span>Python AST + Semgrep</span>

            </footer>

          </div>

        </main>

      </div>

    </div>

  );

}



export default App;
