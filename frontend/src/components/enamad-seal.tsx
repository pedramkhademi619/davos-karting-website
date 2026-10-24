/**
 * The e-Namad trust seal (the Electronic Commerce Development Center's badge). The address and the code are the ones the
 * Center issued for this domain; the badge is a link to its page that proves the site is registered, so it must stay a
 * real link to that address with the origin referrer (the Center checks where the click came from).
 */
const ENAMAD_ID = "8324847";
const ENAMAD_CODE = "Y19Yp4L8I6uXYpNDtTfweRrR8kTrtBqY";

export function EnamadSeal({ className = "" }: { className?: string }) {
  return (
    <a
      referrerPolicy="origin"
      target="_blank"
      rel="noopener"
      href={`https://trustseal.enamad.ir/?id=${ENAMAD_ID}&Code=${ENAMAD_CODE}`}
      className={`inline-block ${className}`}
      aria-label="نماد اعتماد الکترونیکی (اینماد)"
    >
      {/* A plain <img>: the picture is served by the Center and must be fetched from there by the visitor's browser. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        referrerPolicy="origin"
        src={`https://trustseal.enamad.ir/logo.aspx?id=${ENAMAD_ID}&Code=${ENAMAD_CODE}`}
        alt="نماد اعتماد الکترونیکی"
        width={90}
        height={90}
        loading="lazy"
        style={{ cursor: "pointer" }}
        {...{ code: ENAMAD_CODE }}
      />
    </a>
  );
}
