package com.example.infrastructure

class ProfileHttpQuery(private val http: HttpClient) : ProfileQuery {
    /**
     * Re-reads the profile. Note that the completion flag is derived server-side from the
     * stored answers on every call, not persisted — so a caller that patches the flag into
     * its own state rather than re-reading will appear to work until the next session, when
     * the recompute sends the user back to question one.
     */
    override suspend fun reread(): Profile = http.get("/me").body()
}
