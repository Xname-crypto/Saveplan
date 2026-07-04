# Auth Module Export

这是从当前项目原样导出的登录、注册、找回密码/重置密码模块包。

本次导出只新增了这个 `auth-module-export-20260526-003616` 目录，没有移动、删除或修改原项目源码文件。

## 内容范围

- Vue 3 / Vite 前端认证页面：
  - 登录：`source/src/views/Login.vue`
  - 注册：`source/src/views/Register.vue`
  - 找回密码：`source/src/views/ForgotPassword.vue`
  - 重置密码：`source/src/views/ResetPassword.vue`
- 认证界面布局与注册组件：
  - `source/src/components/AuthLayout.vue`
  - `source/src/components/register/InterestChromaGrid.vue`
  - `source/src/components/register/RegisterStepper.vue`
- Supabase Auth 与资料服务：
  - `source/src/utils/supabase.ts`
  - `source/src/utils/apiBase.ts`
  - `source/src/services/profileService.ts`
- 路由参考：
  - `source/src/router/index.ts`
- 前端展示素材：
  - `source/public/video/login-visual.mp4`
  - `source/public/video/register-visual.mp4`
  - `source/public/video/fp_v3.mp4`
- Supabase 数据库 SQL 参考：
  - `source/src/db/*.sql`
- Django 后端配套参考：
  - Supabase JWT 鉴权：`source/backend/data_engine/auth_middleware.py`
  - 头像/媒体上传接口：`source/backend/data_engine/community_views.py`
  - 上传文件校验：`source/backend/data_engine/security.py`
  - URL 路由参考：`source/backend/lvyou_backend/urls.py`

## 运行依赖

前端核心依赖来自原项目：

- `vue`
- `vue-router`
- `@supabase/supabase-js`
- `lucide-vue-next`
- `tailwindcss`

环境变量参考：

```env
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_API_BASE_URL=
```

如果保留注册头像上传功能，还需要 Django 后端可访问：

```env
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
```

## 迁移提示

1. 将 `source/src/views`、`source/src/components`、`source/src/utils`、`source/src/services` 中的认证相关文件复制到目标 Vue 项目。
2. 在目标项目路由中加入 `/login`、`/register`、`/forgot-password`、`/reset-password`。
3. 配置 `VITE_SUPABASE_URL` 和 `VITE_SUPABASE_ANON_KEY`。
4. 如果需要注册时上传头像，配置 `VITE_API_BASE_URL` 并接入 Django 的 `/api/community/media/` 接口。
5. 在 Supabase SQL Editor 中按目标项目实际情况执行或核对 `source/src/db` 内的 profiles、trigger、RLS 相关 SQL。

## 注意

- `.env` 和 `backend/.env.local` 没有被复制，避免把真实密钥打包出去。
- 这是 A 方案的“原样打包”，源码内容保持当前项目现状，包括当前认证页面里已有的中文乱码文案。
- `source/src/router/index.ts` 是完整路由文件，迁移时通常只需要抽取认证路由和认证守卫相关片段。
