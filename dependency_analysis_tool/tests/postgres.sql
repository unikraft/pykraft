--
-- PostgreSQL database dump
--

-- Dumped from database version 11.2 (Debian 11.2-1.pgdg90+1)
-- Dumped by pg_dump version 11.2
SELECT pg_get_functiondef(to_regproc('gen_random_bytes'));
SELECT pg_get_function);
SELECT version();




CREATE SCHEMA IF NOT EXISTS public;

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: admins; Type: TABLE; Schema: public; Owner: gaulthiergain
--

DROP TABLE IF EXISTS public.admins;
DROP TABLE IF EXISTS public.response_values;
DROP TABLE IF EXISTS public.responses;
DROP TABLE IF EXISTS public.surveys;
DROP TABLE IF EXISTS public.users;
DROP TABLE IF EXISTS public.users_surveys;
DROP TABLE IF EXISTS public.surveys_questions;
DROP TABLE IF EXISTS public."values";
DROP TABLE IF EXISTS public.questions;


CREATE TABLE public.admins (
    id_admin text,
    last_name text,
    first_name text,
    phone character varying(20),
    email character varying(255),
    password character varying(255)
);


ALTER TABLE public.admins OWNER TO gaulthiergain;

--
-- Name: questions; Type: TABLE; Schema: public; Owner: gaulthiergain
--

CREATE TABLE public.questions (
    id_question uuid NOT NULL,
    label character varying(255),
    description text,
    type integer
);


ALTER TABLE public.questions OWNER TO gaulthiergain;

--
-- Name: response_values; Type: TABLE; Schema: public; Owner: gaulthiergain
--

CREATE TABLE public.response_values (
    id_value uuid NOT NULL,
    value character varying(255),
    id_response uuid
);


ALTER TABLE public.response_values OWNER TO gaulthiergain;

--
-- Name: responses; Type: TABLE; Schema: public; Owner: gaulthiergain
--

CREATE TABLE public.responses (
    id_response uuid NOT NULL,
    id_question uuid,
    id_survey uuid,
    id_user uuid
);


ALTER TABLE public.responses OWNER TO gaulthiergain;

--
-- Name: surveys; Type: TABLE; Schema: public; Owner: gaulthiergain
--

CREATE TABLE public.surveys (
    id_survey uuid NOT NULL,
    label text,
    description text
);


ALTER TABLE public.surveys OWNER TO gaulthiergain;

--
-- Name: surveys_questions; Type: TABLE; Schema: public; Owner: gaulthiergain
--

CREATE TABLE public.surveys_questions (
    survey_id_survey uuid NOT NULL,
    question_id_question uuid NOT NULL
);


ALTER TABLE public.surveys_questions OWNER TO gaulthiergain;

--
-- Name: users; Type: TABLE; Schema: public; Owner: gaulthiergain
--

CREATE TABLE public.users (
    id_user uuid NOT NULL,
    last_name text,
    first_name text,
    gender character(1),
    birth_date timestamp with time zone,
    phone character varying(20),
    email character varying(255),
    password character varying(255),
    token text
);


ALTER TABLE public.users OWNER TO gaulthiergain;

--
-- Name: users_surveys; Type: TABLE; Schema: public; Owner: gaulthiergain
--

CREATE TABLE public.users_surveys (
    user_id_user uuid NOT NULL,
    survey_id_survey uuid NOT NULL,
    participation_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    completed boolean DEFAULT false
);


ALTER TABLE public.users_surveys OWNER TO gaulthiergain;

--
-- Name: values; Type: TABLE; Schema: public; Owner: gaulthiergain
--

CREATE TABLE public."values" (
    id_value uuid NOT NULL,
    value character varying(255),
    id_question uuid
);


ALTER TABLE public."values" OWNER TO gaulthiergain;

--
-- Data for Name: admins; Type: TABLE DATA; Schema: public; Owner: gaulthiergain
--

COPY public.admins (id_admin, last_name, first_name, phone, email, password) FROM stdin;
u230268	admin	admin	0498761232	admin@admin.com	$2y$10$2yBOMIZHGQxo51L9ZH2zf.jB82WZjGoX41cwkQnVMR5gENVPqhlQe
\.


--
-- Data for Name: questions; Type: TABLE DATA; Schema: public; Owner: gaulthiergain
--

COPY public.questions (id_question, label, description, type) FROM stdin;
20438fb2-eb5d-467e-bfd4-250e89d183c5	Simple checkbox question (survey3)	This is a checkbox question	2
68796251-84e9-46f7-950d-c444c3296f8a	Simple checkbox question (survey1)	This is a checkbox question	2
a7d403e6-9283-4024-81c4-03e1dfe38da9	Simple text question (survey2)	This is a text question	1
e92b183c-ac1c-432a-9714-c0a238fc61a8	Simple text question (survey3)	This is a text question	1
a42f1da2-5596-4dbf-b1b3-a3c726b71470	Simple slider question (survey1)	This is a slider question	3
ce74a375-1b70-428d-835b-b0cd0d41bf60	Simple slider question (survey2)	This is a slider question	3
0bee2abf-7830-4d3f-820d-b63663d68e0e	Simple checkbox question (survey2)	This is a checkbox question	2
01f2d29a-950b-439a-9140-93de3530b74a	Simple slider question (survey3)	This is a slider question	3
43e4d5a5-d83f-4f45-b1ba-9a9393db0386	Simple text question (survey1)	This is a text question	1
1ae727f2-34b2-4f6f-b0aa-edbe64a024fb	How are you? (survey1)	Simple description	2
64c51bc6-84f7-4b12-ae55-8ad7840fe758	Are you hungry? (survey1)	0: No - 5: Yes a lot	3
2174dfe7-5285-4e35-b022-653cc6df91b7	What do you do in your free time? (survey1)	Tell me more	1
4e2cf248-f508-4f13-ab10-b838cbf2a1ca	How’s it going? (survey1)	0: Bad - 10: Great 	3
bac84fdb-761a-465d-ba5d-c188a6fb1980	How was your day?		2
0f820c8e-a1fe-49c0-9d1f-33e92d985ea5	Simple multi-choices questions	Several choices	4
\.


--
-- Data for Name: response_values; Type: TABLE DATA; Schema: public; Owner: gaulthiergain
--

COPY public.response_values (id_value, value, id_response) FROM stdin;
6d2e00da-6ec7-4c18-90ed-7dd4bafb80f0	wqwq	dcda1caf-3886-4408-9b9f-157587d41d2d
35b60a41-842b-4076-98a6-dd4054a7c4a8	0.0	ee69c815-0f2a-478a-836e-ec5e62c7f737
fb119c7a-e375-401e-b181-48a706423a3e	dede	806f8dbb-e2ab-4cde-a91b-f44b3d3bb530
ce3e1f9c-c3ca-49f0-961c-29db4392b0db	0.0	fedce9d1-34b0-47f3-bdec-ca678e610c98
564e4910-a09a-4a43-add5-4c9d43e4a7d5	hihihihi	16d1f544-6704-4e01-b40f-a4038a810857
d2285d06-fff3-493b-aed9-d5dd30d8238b	0.0	d4cb859b-e179-49f7-9556-7bc595484b1d
4c171273-f327-40e2-a12d-88c3f16b87da	value 2	11dce497-081d-438a-b18f-6d4ceb47b85b
94f04dc6-c07e-461e-b994-599107ea8b67	uuuu	e18663a3-79ea-4fe9-b321-6d11d832f108
f191eb2d-9c48-40ea-8d02-724a9691cd34	0.0	cb1b89fe-d6bf-417a-9913-9f5333c7df1c
49fea83b-f351-4138-a02d-5683b88df99d	value 1	0cc71806-a3d1-426f-b562-1e868bc51fa3
a9dbed19-941a-41af-9f7f-6742fb9082d7	jk	c0d06859-3a3d-4759-9de2-b6d90d4e5141
203918b7-cf89-4e2d-9c82-3945f6910939	0.0	f1dc89fe-f5aa-45b3-bec5-c0d7279b7aca
45f4c30a-2474-4205-af54-65c5319345de	hjhjjj	823c2684-fb0c-4e3d-ad8e-817a5b765b57
\.


--
-- Data for Name: responses; Type: TABLE DATA; Schema: public; Owner: gaulthiergain
--

COPY public.responses (id_response, id_question, id_survey, id_user) FROM stdin;
64687575-c83c-45d2-95e5-b03bcdb79020	a7d403e6-9283-4024-81c4-03e1dfe38da9	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
7c35a7ba-6529-4654-8fe2-bf12e4ae346d	a7d403e6-9283-4024-81c4-03e1dfe38da9	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
9ed50bea-03ab-4b10-b22e-43fb5d021947	a7d403e6-9283-4024-81c4-03e1dfe38da9	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
0318006e-1ace-4126-9a65-09f7aeb24ec2	a7d403e6-9283-4024-81c4-03e1dfe38da9	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
d76f1acb-d1a5-4af9-8036-99548dfe76b0	ce74a375-1b70-428d-835b-b0cd0d41bf60	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
51049fc9-fc83-4d95-8d1a-1c1cd2aa7260	0bee2abf-7830-4d3f-820d-b63663d68e0e	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
9fc415df-568d-44b7-a2ae-631d2b14ea03	0f820c8e-a1fe-49c0-9d1f-33e92d985ea5	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
dcda1caf-3886-4408-9b9f-157587d41d2d	a7d403e6-9283-4024-81c4-03e1dfe38da9	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
ee69c815-0f2a-478a-836e-ec5e62c7f737	ce74a375-1b70-428d-835b-b0cd0d41bf60	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
806f8dbb-e2ab-4cde-a91b-f44b3d3bb530	a7d403e6-9283-4024-81c4-03e1dfe38da9	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
fedce9d1-34b0-47f3-bdec-ca678e610c98	ce74a375-1b70-428d-835b-b0cd0d41bf60	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
16d1f544-6704-4e01-b40f-a4038a810857	a7d403e6-9283-4024-81c4-03e1dfe38da9	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
d4cb859b-e179-49f7-9556-7bc595484b1d	ce74a375-1b70-428d-835b-b0cd0d41bf60	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
11dce497-081d-438a-b18f-6d4ceb47b85b	0bee2abf-7830-4d3f-820d-b63663d68e0e	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
e18663a3-79ea-4fe9-b321-6d11d832f108	a7d403e6-9283-4024-81c4-03e1dfe38da9	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
cb1b89fe-d6bf-417a-9913-9f5333c7df1c	ce74a375-1b70-428d-835b-b0cd0d41bf60	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
0cc71806-a3d1-426f-b562-1e868bc51fa3	0bee2abf-7830-4d3f-820d-b63663d68e0e	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
c0d06859-3a3d-4759-9de2-b6d90d4e5141	a7d403e6-9283-4024-81c4-03e1dfe38da9	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
f1dc89fe-f5aa-45b3-bec5-c0d7279b7aca	ce74a375-1b70-428d-835b-b0cd0d41bf60	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
823c2684-fb0c-4e3d-ad8e-817a5b765b57	a7d403e6-9283-4024-81c4-03e1dfe38da9	a6be2a73-68f7-4541-94b8-62a2e61abd12	64f8acd7-ecdb-433a-bd5c-985f6b136eeb
\.


--
-- Data for Name: surveys; Type: TABLE DATA; Schema: public; Owner: gaulthiergain
--

COPY public.surveys (id_survey, label, description) FROM stdin;
074cb506-82fa-4758-af9a-b7fa30b38af3	Example survey 1	This is a simple description for survey 1
a6be2a73-68f7-4541-94b8-62a2e61abd12	Example survey 2	This is a simple description for survey 2
e2c616d8-9867-40c5-953f-63fcaaa29949	Example survey 3	This is a simple description for survey 3
\.


--
-- Data for Name: surveys_questions; Type: TABLE DATA; Schema: public; Owner: gaulthiergain
--

COPY public.surveys_questions (survey_id_survey, question_id_question) FROM stdin;
a6be2a73-68f7-4541-94b8-62a2e61abd12	a7d403e6-9283-4024-81c4-03e1dfe38da9
a6be2a73-68f7-4541-94b8-62a2e61abd12	0bee2abf-7830-4d3f-820d-b63663d68e0e
a6be2a73-68f7-4541-94b8-62a2e61abd12	ce74a375-1b70-428d-835b-b0cd0d41bf60
e2c616d8-9867-40c5-953f-63fcaaa29949	e92b183c-ac1c-432a-9714-c0a238fc61a8
e2c616d8-9867-40c5-953f-63fcaaa29949	01f2d29a-950b-439a-9140-93de3530b74a
e2c616d8-9867-40c5-953f-63fcaaa29949	20438fb2-eb5d-467e-bfd4-250e89d183c5
074cb506-82fa-4758-af9a-b7fa30b38af3	a42f1da2-5596-4dbf-b1b3-a3c726b71470
074cb506-82fa-4758-af9a-b7fa30b38af3	68796251-84e9-46f7-950d-c444c3296f8a
074cb506-82fa-4758-af9a-b7fa30b38af3	43e4d5a5-d83f-4f45-b1ba-9a9393db0386
074cb506-82fa-4758-af9a-b7fa30b38af3	1ae727f2-34b2-4f6f-b0aa-edbe64a024fb
074cb506-82fa-4758-af9a-b7fa30b38af3	64c51bc6-84f7-4b12-ae55-8ad7840fe758
074cb506-82fa-4758-af9a-b7fa30b38af3	2174dfe7-5285-4e35-b022-653cc6df91b7
074cb506-82fa-4758-af9a-b7fa30b38af3	4e2cf248-f508-4f13-ab10-b838cbf2a1ca
074cb506-82fa-4758-af9a-b7fa30b38af3	bac84fdb-761a-465d-ba5d-c188a6fb1980
a6be2a73-68f7-4541-94b8-62a2e61abd12	0f820c8e-a1fe-49c0-9d1f-33e92d985ea5
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: gaulthiergain
--

COPY public.users (id_user, last_name, first_name, gender, birth_date, phone, email, password, token) FROM stdin;
dc3c43d7-a523-408b-9b22-b453e6874375	Garcia	Aiden	F	1778-06-04 12:58:24.152+00	0477217865	garcia.aiden@gmail.com	$2y$10$jbNOFiZ92gg1KyCRheZ3he1NtpPh3lGk41CnuRXy6U1Itk7MV6RcK	\N
283fd95e-a69b-41c0-977d-8d5c84e94a25	Wilson	Anthony	F	1998-06-17 09:55:15.682+00	0498765641	wilson.anthony@gmail.com	$2y$10$ovSmM6oZEQCH3dGkM2qWtOHtBzp9n5wIsrO6JAgATiaix2ZcqgMbC	\N
64f8acd7-ecdb-433a-bd5c-985f6b136eeb	Doe	John	M	1998-06-17 09:55:15.682+00	0498765641	john.doe@gmail.com	$2y$10$xDLTq10ntym/YNbsJcSos.7259sS.y.EVC.v/cpF2wEVWIEo47iD.	\N
16a457f7-4227-4605-be72-d2f02519262c	Smith	James	M	1990-08-22 12:56:44.363+00	0494562132	james.smith@gmail.com	$2y$10$GrfWBZMYMVqdt/aq165HTO7S48BcPUrSavQ0J.bmale0UyfVjOGZ.	\N
c13dd818-66e5-4b4b-9adc-dc6315b87723	Miller	Noah	M	1990-08-22 12:56:44.363+00	0475621313	miller.noah@gmail.com	$2y$10$VEZAmX6mm5lkq9pd8zPnDuPGsBRS3mlQkdOx4uj0THIF7hMX19kp6	\N
3241959c-a33e-4a11-9549-714350548ddb	Dio	Michelle	F	1778-06-04 12:58:24.152+00	0477217865	michelle.dio@gmail.com	$2y$10$SrO1kUUJpT.oPh9ayH1ib.seKa/OrRIv7PwtNqLDLNTp3t..siJ8G	\N
917b18a4-a445-46a7-8f8c-6125cdd24b0c	Jackson	Elijah	M	1998-06-17 09:55:15.682+00	0483762313	jackson.elijag@gmail.com	$2y$10$UItrY1d3iic4ExSdIk761uE.R/YS8RwSdzlVvLV1tmxiExiag6MDi	\N
22236bd1-992c-44b6-ba85-6e96ee144d09	Robinson	William	F	1990-08-22 12:56:44.363+00	0474532112	robinson.william@gmail.com	$2y$10$li4nu3Bxnn6StunsZXe1NuL7cEua9aS.VoLMZFWhqJWEZQRctEuQa	\N
\.


--
-- Data for Name: users_surveys; Type: TABLE DATA; Schema: public; Owner: gaulthiergain
--

COPY public.users_surveys (user_id_user, survey_id_survey, participation_date, completed) FROM stdin;
22236bd1-992c-44b6-ba85-6e96ee144d09	a6be2a73-68f7-4541-94b8-62a2e61abd12	2018-12-23 15:44:15.82+00	f
283fd95e-a69b-41c0-977d-8d5c84e94a25	e2c616d8-9867-40c5-953f-63fcaaa29949	2018-12-23 15:45:00.423+00	f
3241959c-a33e-4a11-9549-714350548ddb	a6be2a73-68f7-4541-94b8-62a2e61abd12	2018-12-23 15:44:29.193+00	f
16a457f7-4227-4605-be72-d2f02519262c	e2c616d8-9867-40c5-953f-63fcaaa29949	2018-12-23 15:45:14.575+00	f
917b18a4-a445-46a7-8f8c-6125cdd24b0c	074cb506-82fa-4758-af9a-b7fa30b38af3	2018-12-23 15:34:22.156+00	f
16a457f7-4227-4605-be72-d2f02519262c	a6be2a73-68f7-4541-94b8-62a2e61abd12	2018-12-23 15:44:37.918+00	f
64f8acd7-ecdb-433a-bd5c-985f6b136eeb	a6be2a73-68f7-4541-94b8-62a2e61abd12	2018-12-23 15:44:48.061+00	f
16a457f7-4227-4605-be72-d2f02519262c	074cb506-82fa-4758-af9a-b7fa30b38af3	2018-12-23 15:34:09.55+00	f
64f8acd7-ecdb-433a-bd5c-985f6b136eeb	074cb506-82fa-4758-af9a-b7fa30b38af3	2018-12-23 15:44:15.939+00	f
\.


--
-- Data for Name: values; Type: TABLE DATA; Schema: public; Owner: gaulthiergain
--

COPY public."values" (id_value, value, id_question) FROM stdin;
928c1dd8-79f7-422c-bd30-079dc50238a5	value 1	0bee2abf-7830-4d3f-820d-b63663d68e0e
52a14543-1cab-4938-9235-85200702fa95	value 2	0bee2abf-7830-4d3f-820d-b63663d68e0e
c89433e8-1501-481f-809c-b02e51085de7	value 3	0bee2abf-7830-4d3f-820d-b63663d68e0e
e9cb3f48-a199-4206-a306-16b064a7b3a2	0	ce74a375-1b70-428d-835b-b0cd0d41bf60
cbe86d49-9e5d-46c1-a4d0-5588bf976a04	10	ce74a375-1b70-428d-835b-b0cd0d41bf60
dec1069a-be4d-4d92-aa8f-b36d0af99888	5	01f2d29a-950b-439a-9140-93de3530b74a
be121954-875c-4578-9e09-d12995de5456	10	01f2d29a-950b-439a-9140-93de3530b74a
0b6cadfd-39c8-4289-a2a2-4debac3992dd	value 1	20438fb2-eb5d-467e-bfd4-250e89d183c5
2933ac47-c5b4-4b71-a49c-b8ff326df60a	value 2	20438fb2-eb5d-467e-bfd4-250e89d183c5
2122de95-5371-49af-802f-7587137756db	0	a42f1da2-5596-4dbf-b1b3-a3c726b71470
84886708-1775-4332-a1a7-6306e4f478f8	20	a42f1da2-5596-4dbf-b1b3-a3c726b71470
7487a867-ce04-4c08-9f3a-76ed2d13b0de	5	a42f1da2-5596-4dbf-b1b3-a3c726b71470
c857fb17-f777-4922-81d1-2b75356a1985	value 1	68796251-84e9-46f7-950d-c444c3296f8a
1f67fb6f-131b-4306-8fd8-a406184b7052	value 2	68796251-84e9-46f7-950d-c444c3296f8a
537eecda-ac22-4891-9892-d408b066c69a	value 3	68796251-84e9-46f7-950d-c444c3296f8a
a5c49b34-dcb5-4d02-b55b-755e635d9c74	value 4	68796251-84e9-46f7-950d-c444c3296f8a
60b48237-d35b-43ac-9e4f-8c34a6f3ab82	Fine 	1ae727f2-34b2-4f6f-b0aa-edbe64a024fb
d1b84605-31c3-409b-849f-881a8a28c780	Not Bad	1ae727f2-34b2-4f6f-b0aa-edbe64a024fb
c1a28cd7-5178-4b71-ae45-d2f599c28186	Bad	1ae727f2-34b2-4f6f-b0aa-edbe64a024fb
a5e56fef-d694-45c6-bae5-7dd40274e36a	0	64c51bc6-84f7-4b12-ae55-8ad7840fe758
0343038f-b8c0-4d27-9144-b0b874b80149	5	64c51bc6-84f7-4b12-ae55-8ad7840fe758
1bdcb37e-2573-4c22-a550-ce304e2f9c67	0	4e2cf248-f508-4f13-ab10-b838cbf2a1ca
60ccf74e-ceb9-4132-94dc-583c5669f71b	10	4e2cf248-f508-4f13-ab10-b838cbf2a1ca
b5c02b57-6e0c-405c-9de8-fafd25a76521	Great! Never better	bac84fdb-761a-465d-ba5d-c188a6fb1980
37e8d248-3ac0-448f-98bc-62145e1ab408	All Right	bac84fdb-761a-465d-ba5d-c188a6fb1980
56717b5d-9435-426d-8ede-248033fcecf7	A little depressed	bac84fdb-761a-465d-ba5d-c188a6fb1980
a71d7040-c39d-4399-87f5-67f755d3a4f4	Bad bad and bad 	bac84fdb-761a-465d-ba5d-c188a6fb1980
e527fa45-d684-467f-9adf-33eabddf6020	Really awful	bac84fdb-761a-465d-ba5d-c188a6fb1980
401b0e97-b43c-43f9-9da9-90107c38dbef	Test 1	0f820c8e-a1fe-49c0-9d1f-33e92d985ea5
94ad963a-a2ad-4da9-a1ad-3b2306e7eb8f	Test 2	0f820c8e-a1fe-49c0-9d1f-33e92d985ea5
953071b6-273f-4823-8741-c82a3a5eda57	Test 4	0f820c8e-a1fe-49c0-9d1f-33e92d985ea5
999fd8e9-4990-464a-a59a-4e07a9f77425	Test 3	0f820c8e-a1fe-49c0-9d1f-33e92d985ea5
17b22adb-e35c-4686-b5e8-eaffb0751112	2	64c51bc6-84f7-4b12-ae55-8ad7840fe758
75654b9c-052d-4a38-a45f-87cd7ddd2fc8	2	4e2cf248-f508-4f13-ab10-b838cbf2a1ca
5fac1ede-efea-4ac5-9b89-96ee0ff6d6d2	2	01f2d29a-950b-439a-9140-93de3530b74a
12b0d4f9-1884-411d-9530-d44f35899af1	2	ce74a375-1b70-428d-835b-b0cd0d41bf60
\.


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: gaulthiergain
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id_question);


--
-- Name: response_values response_values_pkey; Type: CONSTRAINT; Schema: public; Owner: gaulthiergain
--

ALTER TABLE ONLY public.response_values
    ADD CONSTRAINT response_values_pkey PRIMARY KEY (id_value);


--
-- Name: responses responses_pkey; Type: CONSTRAINT; Schema: public; Owner: gaulthiergain
--

ALTER TABLE ONLY public.responses
    ADD CONSTRAINT responses_pkey PRIMARY KEY (id_response);


--
-- Name: surveys surveys_pkey; Type: CONSTRAINT; Schema: public; Owner: gaulthiergain
--

ALTER TABLE ONLY public.surveys
    ADD CONSTRAINT surveys_pkey PRIMARY KEY (id_survey);


--
-- Name: surveys_questions surveys_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: gaulthiergain
--

ALTER TABLE ONLY public.surveys_questions
    ADD CONSTRAINT surveys_questions_pkey PRIMARY KEY (survey_id_survey, question_id_question);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: gaulthiergain
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id_user);


--
-- Name: users_surveys users_surveys_pkey; Type: CONSTRAINT; Schema: public; Owner: gaulthiergain
--

ALTER TABLE ONLY public.users_surveys
    ADD CONSTRAINT users_surveys_pkey PRIMARY KEY (user_id_user, survey_id_survey);


--
-- Name: values values_pkey; Type: CONSTRAINT; Schema: public; Owner: gaulthiergain
--

ALTER TABLE ONLY public."values"
    ADD CONSTRAINT values_pkey PRIMARY KEY (id_value);


--
-- Name: response_values response_values_id_response_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaulthiergain
--

ALTER TABLE ONLY public.response_values
    ADD CONSTRAINT response_values_id_response_fkey FOREIGN KEY (id_response) REFERENCES public.responses(id_response);


--
-- Name: responses responses_id_question_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaulthiergain
--

ALTER TABLE ONLY public.responses
    ADD CONSTRAINT responses_id_question_fkey FOREIGN KEY (id_question) REFERENCES public.questions(id_question);


--
-- Name: responses responses_id_survey_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaulthiergain
--

ALTER TABLE ONLY public.responses
    ADD CONSTRAINT responses_id_survey_fkey FOREIGN KEY (id_survey) REFERENCES public.surveys(id_survey);


--
-- Name: responses responses_id_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaulthiergain
--

ALTER TABLE ONLY public.responses
    ADD CONSTRAINT responses_id_user_fkey FOREIGN KEY (id_user) REFERENCES public.users(id_user);


--
-- Name: values values_id_question_fkey; Type: FK CONSTRAINT; Schema: public; Owner: gaulthiergain
--

ALTER TABLE ONLY public."values"
    ADD CONSTRAINT values_id_question_fkey FOREIGN KEY (id_question) REFERENCES public.questions(id_question);


DROP TABLE IF EXISTS public.admins;
DROP TABLE IF EXISTS public.response_values;
DROP TABLE IF EXISTS public.responses;
DROP TABLE IF EXISTS public.surveys;
DROP TABLE IF EXISTS public.users;
DROP TABLE IF EXISTS public.users_surveys;
DROP TABLE IF EXISTS public.surveys_questions;
DROP TABLE IF EXISTS public."values";
DROP TABLE IF EXISTS public.questions;

