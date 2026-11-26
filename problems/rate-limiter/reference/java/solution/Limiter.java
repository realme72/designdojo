package solution;

/** One client's algorithm. Callers serialise access per client. */
interface Limiter {
    boolean allow(long now);
}
