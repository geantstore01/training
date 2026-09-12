import {guard} from "@/lib/guard";
import {CourseAdmin} from "@/components/course-admin";
export default async function Page(){await guard("administration");return <CourseAdmin/>;}
